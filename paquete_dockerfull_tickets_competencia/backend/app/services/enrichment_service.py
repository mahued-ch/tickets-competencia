import difflib
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models.catalog import ChedrauiProduct, CompetitorProductMapping, NearbyStore
from app.models.enrichment import TicketEnrichment
from app.models.ocr import OcrResult
from app.models.ticket import Ticket, TicketItem, TicketStore, TicketScanFile
from app.schemas.security import SecurityContext
from app.services.security_service import can_view_ticket
from app.services.ticket_service import get_ticket_or_404

MATCH_CONFIDENCE_AUTO = 0.85


def _match_by_upc(db: Session, upc: str) -> ChedrauiProduct | None:
    if not upc:
        return None
    return db.query(ChedrauiProduct).filter(
        ChedrauiProduct.upc == upc, ChedrauiProduct.is_active == True
    ).first()


def _match_by_competitor_code(db: Session, business_code: str, code: str) -> CompetitorProductMapping | None:
    if not code:
        return None
    return db.query(CompetitorProductMapping).filter(
        CompetitorProductMapping.business_code == business_code,
        CompetitorProductMapping.competitor_code == code,
        CompetitorProductMapping.is_active == True,
    ).first()


def _match_fuzzy_by_description(db: Session, business_code: str, description: str) -> list[CompetitorProductMapping]:
    if not description:
        return []
    mappings = db.query(CompetitorProductMapping).filter(
        CompetitorProductMapping.business_code == business_code,
        CompetitorProductMapping.is_active == True,
        CompetitorProductMapping.competitor_description.isnot(None),
    ).all()
    scored = []
    desc_lower = description.lower()
    for m in mappings:
        if not m.competitor_description:
            continue
        ratio = difflib.SequenceMatcher(None, desc_lower, m.competitor_description.lower()).ratio()
        if ratio > 0.5:
            scored.append((m, ratio))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [m for m, _ in scored[:5]]


def _get_chedraui_product_by_mapping(mapping: CompetitorProductMapping) -> ChedrauiProduct | None:
    if mapping.chedraui_product_id:
        return ChedrauiProduct.query.get(mapping.chedraui_product_id)
    return None


def _suggest_for_item(db: Session, business_code: str, item: dict, idx: int) -> dict:
    code = item.get("code")
    description = item.get("description", "")
    upc = item.get("upc")

    product = None
    match_type = None
    confidence = 0.0

    if upc:
        product = _match_by_upc(db, upc)
        if product:
            match_type = "UPC"
            confidence = 0.98

    if not product and code:
        mapping = _match_by_competitor_code(db, business_code, code)
        if mapping and mapping.chedraui_product_id:
            product = db.query(ChedrauiProduct).filter(
                ChedrauiProduct.product_id == mapping.chedraui_product_id
            ).first()
            if product:
                match_type = "CODE"
                confidence = float(mapping.confidence) if mapping.confidence else 0.9

    if not product:
        fuzzy_mappings = _match_fuzzy_by_description(db, business_code, description)
        if fuzzy_mappings:
            best = fuzzy_mappings[0]
            if best.chedraui_product_id:
                product = db.query(ChedrauiProduct).filter(
                    ChedrauiProduct.product_id == best.chedraui_product_id
                ).first()
            if product:
                match_type = best.match_type or "FUZZY"
                confidence = float(best.confidence) if best.confidence else 0.8

    requires_review = confidence < MATCH_CONFIDENCE_AUTO

    return {
        "itemIndex": idx,
        "originalDescription": description,
        "suggestedSku": product.sku if product else None,
        "suggestedUpc": product.upc if product else None,
        "suggestedDescription": product.description if product else description,
        "suggestedListPrice": float(product.list_price) if product and product.list_price else None,
        "suggestedDepartmentCode": product.department_code if product else None,
        "suggestedSubDepartmentCode": product.sub_department_code if product else None,
        "suggestedClassCode": product.class_code if product else None,
        "suggestedSubclassCode": product.subclass_code if product else None,
        "matchedProductId": product.product_id if product else None,
        "matchType": match_type,
        "confidence": confidence,
        "requiresReview": requires_review,
    }


def _find_nearby_stores(db: Session, business_code: str, store_code: str) -> list[str]:
    stores = db.query(NearbyStore).filter(
        NearbyStore.business_code == business_code,
        NearbyStore.store_code == store_code,
        NearbyStore.is_active == True,
    ).all()
    return [s.nearby_chedraui_store_code for s in stores]


def _find_ocr_for_ticket(db: Session, ticket_id: int) -> OcrResult | None:
    sf_ids = [r.ticket_scan_file_id for r in db.query(TicketScanFile).filter(TicketScanFile.ticket_id == ticket_id).all()]
    if not sf_ids:
        return None
    return db.query(OcrResult).filter(OcrResult.ticket_scan_file_id.in_(sf_ids)).order_by(OcrResult.ocr_id.desc()).first()


def run_enrichment(db: Session, ctx: SecurityContext, ticket_id: int) -> dict:
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    active_ocr = _find_ocr_for_ticket(db, ticket_id)

    if not active_ocr:
        raise ValueError("NO_OCR_RESULT")

    existing = db.query(TicketEnrichment).filter(
        TicketEnrichment.ticket_id == ticket_id,
        TicketEnrichment.ocr_result_id == active_ocr.ocr_id,
    ).first()

    if existing:
        return _build_preview(db, ticket, active_ocr, existing)

    extracted = active_ocr.extracted_items or []
    suggestions = [_suggest_for_item(db, ticket.source_business_code, item, idx) for idx, item in enumerate(extracted)]
    nearby = _find_nearby_stores(db, ticket.source_business_code, ticket.source_store_code)
    auto_ok = all(not s["requiresReview"] for s in suggestions)
    status = "COMPLETED" if auto_ok else "REVIEW"

    enrichment = TicketEnrichment(
        ticket_id=ticket_id,
        ocr_result_id=active_ocr.ocr_id,
        status=status,
    )
    db.add(enrichment)
    db.commit()
    db.refresh(enrichment)

    if auto_ok:
        _apply_enrichment(db, ctx, enrichment, suggestions, nearby)

    return {
        "enrichmentId": enrichment.enrichment_id,
        "ticketId": ticket_id,
        "ocrResultId": active_ocr.ocr_id,
        "status": enrichment.status,
        "rawText": active_ocr.raw_text,
        "extractedItems": extracted,
        "suggestions": suggestions,
        "nearbyStoreCodes": nearby,
    }


def get_enrichment_preview(db: Session, ctx: SecurityContext, ticket_id: int) -> dict | None:
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    active_ocr = _find_ocr_for_ticket(db, ticket_id)

    if not active_ocr:
        return None

    enrichment = db.query(TicketEnrichment).filter(
        TicketEnrichment.ticket_id == ticket_id,
        TicketEnrichment.ocr_result_id == active_ocr.ocr_id,
    ).first()

    if not enrichment:
        return None

    return _build_preview(db, ticket, active_ocr, enrichment)


def _build_preview(db: Session, ticket: Ticket, ocr: OcrResult, enrichment: TicketEnrichment) -> dict:
    extracted = ocr.extracted_items or []
    suggestions = [_suggest_for_item(db, ticket.source_business_code, item, idx) for idx, item in enumerate(extracted)]
    nearby = _find_nearby_stores(db, ticket.source_business_code, ticket.source_store_code)
    return {
        "enrichmentId": enrichment.enrichment_id,
        "ticketId": ticket.ticket_id,
        "ocrResultId": ocr.ocr_id,
        "status": enrichment.status,
        "rawText": ocr.raw_text,
        "extractedItems": extracted,
        "suggestions": suggestions,
        "nearbyStoreCodes": nearby,
    }


def update_enrichment_items(db: Session, ctx: SecurityContext, ticket_id: int, items: list[dict]) -> dict:
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    active_ocr = _find_ocr_for_ticket(db, ticket_id)

    if not active_ocr:
        raise ValueError("NO_OCR_RESULT")

    enrichment = db.query(TicketEnrichment).filter(
        TicketEnrichment.ticket_id == ticket_id,
        TicketEnrichment.ocr_result_id == active_ocr.ocr_id,
    ).first()

    if not enrichment:
        raise ValueError("NO_ENRICHMENT_IN_PROGRESS")

    if enrichment.status == "COMPLETED":
        raise ValueError("ENRICHMENT_ALREADY_COMPLETED")

    extracted = active_ocr.extracted_items or []
    for update in items:
        idx = update.get("itemIndex")
        if idx is not None and 0 <= idx < len(extracted):
            for key in ("sku", "upc", "description", "quantity", "unitPrice", "lineAmount",
                        "departmentCode", "subDepartmentCode", "classCode", "subclassCode"):
                if key in update and update[key] is not None:
                    extracted[idx][key] = update[key]

    active_ocr.extracted_items = extracted
    db.commit()

    suggestions = [_suggest_for_item(db, ticket.source_business_code, item, idx) for idx, item in enumerate(extracted)]
    nearby = _find_nearby_stores(db, ticket.source_business_code, ticket.source_store_code)

    return {
        "enrichmentId": enrichment.enrichment_id,
        "ticketId": ticket_id,
        "ocrResultId": active_ocr.ocr_id,
        "status": enrichment.status,
        "rawText": active_ocr.raw_text,
        "extractedItems": extracted,
        "suggestions": suggestions,
        "nearbyStoreCodes": nearby,
    }


def confirm_enrichment(db: Session, ctx: SecurityContext, ticket_id: int, notes: str | None = None, items: list[dict] | None = None) -> dict:
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    active_ocr = _find_ocr_for_ticket(db, ticket_id)

    if not active_ocr:
        raise ValueError("NO_OCR_RESULT")

    enrichment = db.query(TicketEnrichment).filter(
        TicketEnrichment.ticket_id == ticket_id,
        TicketEnrichment.ocr_result_id == active_ocr.ocr_id,
    ).first()

    if not enrichment:
        raise ValueError("NO_ENRICHMENT_IN_PROGRESS")

    if enrichment.status == "COMPLETED":
        raise ValueError("ENRICHMENT_ALREADY_COMPLETED")

    if items:
        extracted = active_ocr.extracted_items or []
        for update in items:
            idx = update.get("itemIndex")
            if idx is not None and 0 <= idx < len(extracted):
                for key in ("sku", "upc", "description", "quantity", "unitPrice", "lineAmount",
                            "departmentCode", "subDepartmentCode", "classCode", "subclassCode"):
                    if key in update and update[key] is not None:
                        extracted[idx][key] = update[key]
        active_ocr.extracted_items = extracted

    enrichment.status = "COMPLETED"
    enrichment.reviewed_by_user_id = ctx.user_id
    enrichment.reviewed_at = func.now()
    enrichment.notes = notes

    suggestions = [_suggest_for_item(db, ticket.source_business_code, item, idx)
                   for idx, item in enumerate(active_ocr.extracted_items or [])]
    nearby = _find_nearby_stores(db, ticket.source_business_code, ticket.source_store_code)

    _apply_enrichment(db, ctx, enrichment, suggestions, nearby)
    db.commit()

    return {"status": "COMPLETED", "enrichmentId": enrichment.enrichment_id, "ticketId": ticket_id}


def reject_enrichment(db: Session, ctx: SecurityContext, ticket_id: int, notes: str | None = None) -> dict:
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    active_ocr = _find_ocr_for_ticket(db, ticket_id)

    if not active_ocr:
        raise ValueError("NO_OCR_RESULT")

    enrichment = db.query(TicketEnrichment).filter(
        TicketEnrichment.ticket_id == ticket_id,
        TicketEnrichment.ocr_result_id == active_ocr.ocr_id,
    ).first()

    if not enrichment:
        raise ValueError("NO_ENRICHMENT_IN_PROGRESS")

    enrichment.status = "REJECTED"
    enrichment.reviewed_by_user_id = ctx.user_id
    enrichment.reviewed_at = func.now()
    enrichment.notes = notes
    db.commit()

    return {"status": "REJECTED", "enrichmentId": enrichment.enrichment_id, "ticketId": ticket_id}


def _apply_enrichment(db: Session, ctx: SecurityContext, enrichment: TicketEnrichment,
                       suggestions: list[dict], nearby_store_codes: list[str]) -> None:
    ticket = db.query(Ticket).filter(Ticket.ticket_id == enrichment.ticket_id).first()
    if not ticket:
        return

    existing_items = {i.item_sequence: i for i in db.query(TicketItem).filter(TicketItem.ticket_id == ticket.ticket_id).all()}
    existing_stores = {s.store_code for s in db.query(TicketStore).filter(TicketStore.ticket_id == ticket.ticket_id).all()}
    max_seq = max(existing_items.keys()) if existing_items else 0

    for idx, s in enumerate(suggestions):
        seq = idx + 1
        item = existing_items.get(seq)
        if item:
            if s.get("suggestedSku"):
                item.product_code = s["suggestedSku"]
            if s.get("suggestedDescription"):
                item.product_description = s["suggestedDescription"]
            if s.get("suggestedUpc"):
                item.upc = s["suggestedUpc"]
            if s.get("suggestedDepartmentCode"):
                item.department_code = s["suggestedDepartmentCode"]
            if s.get("suggestedSubDepartmentCode"):
                item.sub_department_code = s["suggestedSubDepartmentCode"]
            if s.get("suggestedClassCode"):
                item.class_code = s["suggestedClassCode"]
            if s.get("suggestedSubclassCode"):
                item.subclass_code = s["suggestedSubclassCode"]
        else:
            new_item = TicketItem(
                ticket_id=ticket.ticket_id,
                item_sequence=seq,
                product_code=s.get("suggestedSku"),
                product_description=s.get("suggestedDescription"),
                upc=s.get("suggestedUpc"),
                department_code=s.get("suggestedDepartmentCode"),
                sub_department_code=s.get("suggestedSubDepartmentCode"),
                class_code=s.get("suggestedClassCode"),
                subclass_code=s.get("suggestedSubclassCode"),
            )
            db.add(new_item)

    for store_code in nearby_store_codes:
        if store_code not in existing_stores:
            ts = TicketStore(ticket_id=ticket.ticket_id, store_code=store_code)
            db.add(ts)
