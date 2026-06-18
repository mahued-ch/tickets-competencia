from sqlalchemy.orm import Session, joinedload
from app.models.ticket import Ticket
from app.schemas.ticket import TicketItemDTO, TicketStoreDTO, TicketSummaryDTO, ScanFileDTO
from app.services.security_service import can_view_ticket
from app.schemas.security import SecurityContext


def _ticket_to_dto(ticket: Ticket) -> TicketSummaryDTO:
    return TicketSummaryDTO(
        ticketId=ticket.ticket_id,
        sourceTicketCode=ticket.source_ticket_code,
        sourceBusinessCode=ticket.source_business_code,
        sourceStoreCode=ticket.source_store_code,
        sourceTicketDate=ticket.source_ticket_date,
        sourceTicketKey=ticket.source_ticket_key,
        sourceStatusCode=ticket.source_status_code,
        scanStatus=ticket.scan_status,
        hasScanFile=ticket.has_scan_file,
        createdAt=ticket.created_at,
        updatedAt=ticket.updated_at,
    )


def search_tickets(db: Session, ctx: SecurityContext, filters: dict) -> tuple[list[TicketSummaryDTO], dict]:
    query = db.query(Ticket).options(joinedload(Ticket.stores))
    if value := filters.get("sourceTicketKey"):
        query = query.filter(Ticket.source_ticket_key == value)
    if value := filters.get("sourceStatusCode"):
        query = query.filter(Ticket.source_status_code == value)
    if value := filters.get("scanStatus"):
        query = query.filter(Ticket.scan_status == value)
    if value := filters.get("sourceTicketDateFrom"):
        query = query.filter(Ticket.source_ticket_date >= value)
    if value := filters.get("sourceTicketDateTo"):
        query = query.filter(Ticket.source_ticket_date <= value)

    rows = query.order_by(Ticket.source_ticket_date.desc()).all()
    visible = [r for r in rows if can_view_ticket(ctx, r)]
    page = int(filters.get("page", 1))
    page_size = int(filters.get("pageSize", 20))
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = visible[start:end]
    total = len(visible)
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    return [ _ticket_to_dto(r) for r in page_rows ], {
        "page": page,
        "pageSize": page_size,
        "totalRecords": total,
        "totalPages": total_pages,
    }


def get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.query(Ticket).options(joinedload(Ticket.items), joinedload(Ticket.stores), joinedload(Ticket.scan_files)).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise LookupError("Ticket not found")
    return ticket


def get_ticket_detail(db: Session, ctx: SecurityContext, ticket_id: int):
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")
    active = next((f for f in sorted(ticket.scan_files, key=lambda x: x.version_number, reverse=True) if f.is_active), None)
    scan_summary = None
    if active:
        scan_summary = {
            "exists": True,
            "isConfirmed": active.is_confirmed,
            "versionNumber": int(active.version_number),
            "fileName": active.file_name,
            "mimeType": active.mime_type,
            "uploadedAt": active.uploaded_at,
        }
    else:
        scan_summary = {"exists": False}
    return {"ticket": _ticket_to_dto(ticket), "scanFileSummary": scan_summary}


def get_ticket_items(db: Session, ctx: SecurityContext, ticket_id: int):
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")
    return [
        TicketItemDTO(
            ticketItemId=i.ticket_item_id,
            ticketId=i.ticket_id,
            itemSequence=int(i.item_sequence),
            productCode=i.product_code,
            productDescription=i.product_description,
            quantity=float(i.quantity) if i.quantity is not None else None,
            unitPrice=float(i.unit_price) if i.unit_price is not None else None,
            lineAmount=float(i.line_amount) if i.line_amount is not None else None,
        )
        for i in ticket.items
    ]


def get_ticket_stores(db: Session, ctx: SecurityContext, ticket_id: int):
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")
    return [TicketStoreDTO(ticketStoreId=s.ticket_store_id, ticketId=s.ticket_id, storeCode=s.store_code) for s in ticket.stores]


def get_active_scan_file(db: Session, ctx: SecurityContext, ticket_id: int):
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")
    active = next((f for f in sorted(ticket.scan_files, key=lambda x: x.version_number, reverse=True) if f.is_active), None)
    if not active:
        return None
    return ScanFileDTO(
        ticketScanFileId=active.ticket_scan_file_id,
        ticketId=active.ticket_id,
        fileName=active.file_name,
        fileExtension=active.file_extension,
        mimeType=active.mime_type,
        fileSizeBytes=int(active.file_size_bytes),
        fileHash=active.file_hash,
        storagePath=active.storage_path,
        storageProvider=active.storage_provider,
        versionNumber=int(active.version_number),
        isActive=active.is_active,
        isConfirmed=active.is_confirmed,
        uploadedByUserId=active.uploaded_by_user_id,
        uploadedAt=active.uploaded_at,
        confirmedByUserId=active.confirmed_by_user_id,
        confirmedAt=active.confirmed_at,
        notes=active.notes,
    )
