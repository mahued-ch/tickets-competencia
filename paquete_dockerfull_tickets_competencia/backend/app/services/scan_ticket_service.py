import json
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.core.config import get_settings
from app.models.catalog import ChedrauiProduct, CompetitorProductMapping
from app.models.enrichment import TicketEnrichment
from app.models.ocr import OcrResult
from app.models.ticket import Ticket, TicketItem, TicketStore, TicketScanFile
from app.schemas.security import SecurityContext
from app.services.security_service import can_view_ticket
from app.services.ticket_service import get_ticket_or_404
from app.services.ocr_service import trigger_ocr, get_ocr_result
from app.services.enrichment_service import (
    _suggest_for_item, _find_nearby_stores, _apply_enrichment, MATCH_CONFIDENCE_AUTO
)
from app.storage.local_storage import LocalStorageService

settings = get_settings()
storage = LocalStorageService()


def _generate_scan_code() -> str:
    now = datetime.now()
    return f"SCAN-{now.strftime('%Y%m%d%H%M%S')}-{now.microsecond // 1000:03d}"


def _build_source_ticket_key(ticket_code: str, business_code: str, store_code: str, ticket_date: date) -> str:
    return f"{ticket_code}|{business_code}|{store_code}|{ticket_date.strftime('%Y%m%d')}"


def _get_or_create_chedraui_product(db: Session, item: dict) -> int | None:
    upc = item.get("upc")
    sku = item.get("sku") or upc
    description = item.get("description")
    if not sku and not upc:
        return None
    product = None
    if upc:
        product = db.query(ChedrauiProduct).filter(
            ChedrauiProduct.upc == upc, ChedrauiProduct.is_active == True
        ).first()
    if not product and sku:
        product = db.query(ChedrauiProduct).filter(
            ChedrauiProduct.sku == sku, ChedrauiProduct.is_active == True
        ).first()
    if product:
        return product.product_id
    product = ChedrauiProduct(
        sku=sku or upc,
        upc=upc,
        description=description,
        list_price=item.get("unitPrice"),
        department_code=item.get("departmentCode"),
        sub_department_code=item.get("subDepartmentCode"),
        class_code=item.get("classCode"),
        subclass_code=item.get("subclassCode"),
        is_active=True,
    )
    db.add(product)
    db.flush()
    return product.product_id


def _upsert_competitor_mapping(db: Session, business_code: str, item: dict, chedraui_product_id: int | None) -> None:
    competitor_code = item.get("code")
    competitor_description = item.get("description")
    if not competitor_code and not competitor_description:
        return
    existing = db.query(CompetitorProductMapping).filter(
        CompetitorProductMapping.business_code == business_code,
        CompetitorProductMapping.competitor_code == competitor_code,
        CompetitorProductMapping.is_active == True,
    ).first() if competitor_code else None
    if existing:
        if competitor_description:
            existing.competitor_description = competitor_description
        if chedraui_product_id:
            existing.chedraui_product_id = chedraui_product_id
        return
    mapping = CompetitorProductMapping(
        business_code=business_code,
        competitor_code=competitor_code,
        competitor_description=competitor_description,
        chedraui_product_id=chedraui_product_id,
        match_type="MANUAL",
        confidence=1.0,
        is_active=True,
    )
    db.add(mapping)


def create_ticket_from_scan(
    db: Session, ctx: SecurityContext, file_content: bytes, file_name: str,
    business_code: str, store_code: str,
) -> dict:
    ticket_code = _generate_scan_code()
    ticket_date = date.today()
    source_key = _build_source_ticket_key(ticket_code, business_code, store_code, ticket_date)

    ticket = Ticket(
        source_ticket_code=ticket_code,
        source_business_code=business_code,
        source_store_code=store_code,
        source_ticket_date=ticket_date,
        source_ticket_key=source_key,
        source_status_code='9',
        scan_status='NO_FILE',
        has_scan_file=False,
    )
    db.add(ticket)
    db.flush()

    stored = storage.save_ticket_file(ticket.ticket_id, file_name, file_content)

    result = db.execute(
        text("""
            SELECT new_ticket_scan_file_id, new_version_number
            FROM competitor_ticket.fn_replace_ticket_scan_file(
                p_ticket_id => :ticket_id,
                p_file_name => :file_name,
                p_file_extension => :ext,
                p_mime_type => :mime,
                p_file_size_bytes => :size,
                p_file_hash => :hash,
                p_storage_path => :path,
                p_uploaded_by_user_id => :user_id,
                p_storage_provider => :provider,
                p_notes => :notes
            )
        """),
        {
            'ticket_id': ticket.ticket_id,
            'file_name': stored['file_name'],
            'ext': stored['extension'],
            'mime': stored['mime_type'],
            'size': stored['size'],
            'hash': stored['hash'],
            'path': stored['path'],
            'provider': stored['provider'],
            'user_id': ctx.user_id,
            'notes': 'Created from scan',
        },
    )
    sf_row = result.fetchone()
    db.flush()

    confirm_result = db.execute(
        text("""
            SELECT ticket_scan_file_id, ticket_id, version_number, confirmed_at
            FROM competitor_ticket.fn_confirm_ticket_scan_file(
                p_ticket_id => :ticket_id,
                p_confirmed_by_user_id => :user_id,
                p_notes => :notes
            )
        """),
        {'ticket_id': ticket.ticket_id, 'user_id': ctx.user_id, 'notes': 'Auto-confirmed from scan'},
    )
    confirm_row = confirm_result.fetchone()
    db.commit()

    db.refresh(ticket)

    try:
        ocr_data = trigger_ocr(db, ctx, ticket.ticket_id)
    except Exception:
        ocr_data = None

    enrichment_data = None
    if ocr_data:
        try:
            active_ocr = db.query(OcrResult).filter(
                OcrResult.ocr_id == ocr_data['ocrId']
            ).first()
            if active_ocr:
                extracted = active_ocr.extracted_items or []
                suggestions = [_suggest_for_item(db, business_code, item, idx) for idx, item in enumerate(extracted)]
                nearby = _find_nearby_stores(db, business_code, store_code)
                auto_ok = all(not s["requiresReview"] for s in suggestions)
                status = "COMPLETED" if auto_ok else "REVIEW"

                enrichment = TicketEnrichment(
                    ticket_id=ticket.ticket_id,
                    ocr_result_id=active_ocr.ocr_id,
                    status=status,
                )
                db.add(enrichment)
                db.commit()
                db.refresh(enrichment)

                if auto_ok:
                    _apply_enrichment(db, ctx, enrichment, suggestions, nearby)

                enrichment_data = {
                    "enrichmentId": enrichment.enrichment_id,
                    "status": enrichment.status,
                    "extractedItems": extracted,
                    "suggestions": suggestions,
                    "nearbyStoreCodes": nearby,
                }
        except Exception:
            db.rollback()
            db.refresh(ticket)

    return {
        "ticketId": ticket.ticket_id,
        "sourceTicketCode": ticket.source_ticket_code,
        "sourceBusinessCode": ticket.source_business_code,
        "sourceStoreCode": ticket.source_store_code,
        "sourceTicketDate": ticket.source_ticket_date.isoformat(),
        "scanStatus": ticket.scan_status,
        "hasScanFile": ticket.has_scan_file,
        "ocr": ocr_data,
        "enrichment": enrichment_data,
    }


def get_scan_ticket_detail(db: Session, ctx: SecurityContext, ticket_id: int) -> dict | None:
    ticket = db.query(Ticket).filter(
        Ticket.ticket_id == ticket_id, Ticket.batch_id.is_(None)
    ).first()
    if not ticket:
        return None
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    ocr_result = get_ocr_result(db, ctx, ticket_id)

    enrichment = None
    suggestions = []
    nearby = []
    if ocr_result:
        active_ocr = db.query(OcrResult).filter(
            OcrResult.ocr_id == ocr_result['ocrId']
        ).first()
        if active_ocr:
            extracted = active_ocr.extracted_items or []
            suggestions = [_suggest_for_item(db, ticket.source_business_code, item, idx) for idx, item in enumerate(extracted)]
            nearby = _find_nearby_stores(db, ticket.source_business_code, ticket.source_store_code)
            enrichment_row = db.query(TicketEnrichment).filter(
                TicketEnrichment.ticket_id == ticket_id,
                TicketEnrichment.ocr_result_id == active_ocr.ocr_id,
            ).first()
            if enrichment_row:
                enrichment = {
                    "enrichmentId": enrichment_row.enrichment_id,
                    "status": enrichment_row.status,
                }

    return {
        "ticketId": ticket.ticket_id,
        "sourceTicketCode": ticket.source_ticket_code,
        "sourceBusinessCode": ticket.source_business_code,
        "sourceStoreCode": ticket.source_store_code,
        "sourceTicketDate": ticket.source_ticket_date.isoformat(),
        "scanStatus": ticket.scan_status,
        "hasScanFile": ticket.has_scan_file,
        "ocr": ocr_result,
        "enrichment": enrichment,
        "suggestions": suggestions,
        "nearbyStoreCodes": nearby,
    }


def update_scan_ticket_items(
    db: Session, ctx: SecurityContext, ticket_id: int, items: list[dict],
    business_code: str | None = None, store_code: str | None = None,
) -> dict:
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    if business_code:
        ticket.source_business_code = business_code
    if store_code:
        ticket.source_store_code = store_code

    active_ocr = db.query(OcrResult).filter(
        OcrResult.ticket_scan_file_id.in_(
            db.query(TicketScanFile.ticket_scan_file_id).filter(
                TicketScanFile.ticket_id == ticket_id
            )
        )
    ).order_by(OcrResult.ocr_id.desc()).first()

    if active_ocr:
        extracted = active_ocr.extracted_items or []
        for update in items:
            idx = update.get("itemIndex")
            if idx is not None and 0 <= idx < len(extracted):
                for key in ("code", "description", "quantity", "unitPrice", "lineAmount",
                            "sku", "upc", "departmentCode", "subDepartmentCode", "classCode", "subclassCode"):
                    if key in update and update[key] is not None:
                        extracted[idx][key] = update[key]
        active_ocr.extracted_items = extracted

    db.commit()
    db.refresh(ticket)

    suggestions = []
    nearby = []
    if active_ocr:
        extracted = active_ocr.extracted_items or []
        suggestions = [_suggest_for_item(db, ticket.source_business_code, item, idx) for idx, item in enumerate(extracted)]
        nearby = _find_nearby_stores(db, ticket.source_business_code, ticket.source_store_code)

    return {
        "ticketId": ticket.ticket_id,
        "sourceBusinessCode": ticket.source_business_code,
        "sourceStoreCode": ticket.source_store_code,
        "suggestions": suggestions,
        "nearbyStoreCodes": nearby,
    }


def finalize_scan_ticket(
    db: Session, ctx: SecurityContext, ticket_id: int,
    items: list[dict] | None = None,
    business_code: str | None = None, store_code: str | None = None,
) -> dict:
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    if business_code:
        ticket.source_business_code = business_code
    if store_code:
        ticket.source_store_code = store_code

    active_ocr = db.query(OcrResult).filter(
        OcrResult.ticket_scan_file_id.in_(
            db.query(TicketScanFile.ticket_scan_file_id).filter(
                TicketScanFile.ticket_id == ticket_id
            )
        )
    ).order_by(OcrResult.ocr_id.desc()).first()

    if not active_ocr:
        raise ValueError("NO_OCR_RESULT")

    extracted = active_ocr.extracted_items or []
    if items:
        for update in items:
            idx = update.get("itemIndex")
            if idx is not None and 0 <= idx < len(extracted):
                for key in ("code", "description", "quantity", "unitPrice", "lineAmount",
                            "sku", "upc", "departmentCode", "subDepartmentCode", "classCode", "subclassCode"):
                    if key in update and update[key] is not None:
                        extracted[idx][key] = update[key]
        active_ocr.extracted_items = extracted

    suggestions = [_suggest_for_item(db, ticket.source_business_code, item, idx) for idx, item in enumerate(extracted)]
    nearby = _find_nearby_stores(db, ticket.source_business_code, ticket.source_store_code)

    enrichment = db.query(TicketEnrichment).filter(
        TicketEnrichment.ticket_id == ticket_id,
        TicketEnrichment.ocr_result_id == active_ocr.ocr_id,
    ).first()
    if not enrichment:
        enrichment = TicketEnrichment(
            ticket_id=ticket_id,
            ocr_result_id=active_ocr.ocr_id,
            status="REVIEW",
        )
        db.add(enrichment)
        db.flush()

    enrichment.status = "COMPLETED"
    enrichment.reviewed_by_user_id = ctx.user_id
    enrichment.reviewed_at = func.now()

    _apply_enrichment(db, ctx, enrichment, suggestions, nearby)
    db.flush()

    catalog_updates = []
    for idx, item in enumerate(extracted):
        sug = suggestions[idx] if idx < len(suggestions) else {}
        if sug.get("requiresReview") or not sug.get("matchedProductId"):
            chedraui_id = _get_or_create_chedraui_product(db, item)
            _upsert_competitor_mapping(db, ticket.source_business_code, item, chedraui_id)
            if chedraui_id:
                catalog_updates.append({"itemIndex": idx, "chedrauiProductId": chedraui_id})

    db.commit()
    db.refresh(ticket)

    return {
        "ticketId": ticket.ticket_id,
        "sourceTicketCode": ticket.source_ticket_code,
        "sourceBusinessCode": ticket.source_business_code,
        "sourceStoreCode": ticket.source_store_code,
        "scanStatus": ticket.scan_status,
        "hasScanFile": ticket.has_scan_file,
        "itemCount": len(extracted),
        "catalogUpdates": catalog_updates,
    }


def list_scan_tickets(db: Session, ctx: SecurityContext, filters: dict) -> tuple[list[dict], dict]:
    query = db.query(Ticket).filter(Ticket.batch_id.is_(None))

    if value := filters.get("sourceBusinessCode"):
        query = query.filter(Ticket.source_business_code == value)
    if value := filters.get("sourceStoreCode"):
        query = query.filter(Ticket.source_store_code == value)
    if value := filters.get("sourceTicketDateFrom"):
        query = query.filter(Ticket.source_ticket_date >= value)
    if value := filters.get("sourceTicketDateTo"):
        query = query.filter(Ticket.source_ticket_date <= value)

    rows = query.order_by(Ticket.created_at.desc()).all()
    visible = [r for r in rows if can_view_ticket(ctx, r)]

    page = int(filters.get("page", 1))
    page_size = int(filters.get("pageSize", 20))
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = visible[start:end]
    total = len(visible)
    total_pages = (total + page_size - 1) // page_size if page_size else 1

    data = [{
        "ticketId": r.ticket_id,
        "sourceTicketCode": r.source_ticket_code,
        "sourceBusinessCode": r.source_business_code,
        "sourceStoreCode": r.source_store_code,
        "sourceTicketDate": r.source_ticket_date.isoformat(),
        "scanStatus": r.scan_status,
        "hasScanFile": r.has_scan_file,
        "createdAt": r.created_at,
    } for r in page_rows]

    return data, {
        "page": page,
        "pageSize": page_size,
        "totalRecords": total,
        "totalPages": total_pages,
    }
