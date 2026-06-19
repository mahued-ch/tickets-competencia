from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.ticket import Ticket
from app.schemas.security import SecurityContext
from app.services.security_service import can_view_ticket
from app.services.ticket_service import get_ticket_or_404


def validate_upload_basics(ticket: Ticket, ctx: SecurityContext) -> None:
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")
    if ticket.source_status_code != '9':
        raise ValueError("SCAN_UPLOAD_NOT_ALLOWED_BY_SOURCE_STATUS")


def upload_or_replace_scan_file(db: Session, ctx: SecurityContext, ticket_id: int, stored_file: dict, notes: str | None = None):
    ticket = get_ticket_or_404(db, ticket_id)
    validate_upload_basics(ticket, ctx)

    # enforce pre-check: already confirmed (the function also checks, but fail fast)
    from app.models.ticket import TicketScanFile
    active = db.query(TicketScanFile).filter(TicketScanFile.ticket_id == ticket_id, TicketScanFile.is_active == True).order_by(TicketScanFile.version_number.desc()).first()
    if active and active.is_confirmed:
        raise ValueError("SCAN_FILE_ALREADY_CONFIRMED")

    result = db.execute(
        text("""
            SELECT new_ticket_scan_file_id, new_version_number, previous_ticket_scan_file_id
            FROM competitor_ticket.fn_replace_ticket_scan_file(
                p_ticket_id => :ticket_id,
                p_file_name => :file_name,
                p_file_extension => :file_extension,
                p_mime_type => :mime_type,
                p_file_size_bytes => :file_size_bytes,
                p_file_hash => :file_hash,
                p_storage_path => :storage_path,
                p_uploaded_by_user_id => :user_id,
                p_storage_provider => :storage_provider,
                p_notes => :notes
            )
        """),
        {
            'ticket_id': ticket_id,
            'file_name': stored_file['file_name'],
            'file_extension': stored_file['extension'],
            'mime_type': stored_file['mime_type'],
            'file_size_bytes': stored_file['size'],
            'file_hash': stored_file['hash'],
            'storage_path': stored_file['path'],
            'storage_provider': stored_file['provider'],
            'user_id': ctx.user_id,
            'notes': notes,
        },
    )
    row = result.fetchone()
    db.commit()

    # refresh ticket to get updated scan_status from trigger
    db.refresh(ticket)
    return {
        'ticketScanFileId': row.new_ticket_scan_file_id,
        'ticketId': ticket_id,
        'versionNumber': row.new_version_number,
        'previousTicketScanFileId': row.previous_ticket_scan_file_id,
        'scanStatus': ticket.scan_status,
        'hasScanFile': ticket.has_scan_file,
    }


def confirm_scan_file(db: Session, ctx: SecurityContext, ticket_id: int, notes: str | None = None):
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    result = db.execute(
        text("""
            SELECT ticket_scan_file_id, ticket_id, version_number, confirmed_at
            FROM competitor_ticket.fn_confirm_ticket_scan_file(
                p_ticket_id => :ticket_id,
                p_confirmed_by_user_id => :user_id,
                p_notes => :notes
            )
        """),
        {
            'ticket_id': ticket_id,
            'user_id': ctx.user_id,
            'notes': notes,
        },
    )
    row = result.fetchone()
    if not row:
        raise LookupError("ACTIVE_SCAN_FILE_NOT_FOUND")
    db.commit()

    # refresh ticket to get updated scan_status from trigger
    db.refresh(ticket)
    return {
        'ticketScanFileId': row.ticket_scan_file_id,
        'ticketId': row.ticket_id,
        'versionNumber': row.version_number,
        'confirmedAt': row.confirmed_at,
        'scanStatus': ticket.scan_status,
        'hasScanFile': ticket.has_scan_file,
    }
