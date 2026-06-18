from sqlalchemy.orm import Session
from datetime import datetime
from app.models.ticket import TicketScanFile, AuditEvent
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

    active = db.query(TicketScanFile).filter(TicketScanFile.ticket_id == ticket_id, TicketScanFile.is_active == True).order_by(TicketScanFile.version_number.desc()).first()
    if active and active.is_confirmed:
        raise ValueError("SCAN_FILE_ALREADY_CONFIRMED")

    previous_id = None
    next_version = 1
    if active:
        active.is_active = False
        previous_id = active.ticket_scan_file_id
        next_version = int(active.version_number) + 1

    row = TicketScanFile(
        ticket_id=ticket_id,
        file_name=stored_file['file_name'],
        file_extension=stored_file['extension'],
        mime_type=stored_file['mime_type'],
        file_size_bytes=stored_file['size'],
        file_hash=stored_file['hash'],
        storage_path=stored_file['path'],
        storage_provider=stored_file['provider'],
        version_number=next_version,
        is_active=True,
        is_confirmed=False,
        uploaded_by_user_id=ctx.user_id,
        notes=notes,
    )
    db.add(row)
    db.flush()
    if active:
        active.replaced_by_file_id = row.ticket_scan_file_id
    ticket.has_scan_file = True
    ticket.scan_status = 'FILE_UPLOADED'
    ticket.updated_at = datetime.utcnow()
    db.add(AuditEvent(
        event_type='SCAN_FILE_REPLACED' if previous_id else 'SCAN_FILE_UPLOADED',
        entity_name='ticket_scan_file',
        entity_id=row.ticket_scan_file_id,
        source_ticket_key=ticket.source_ticket_key,
        user_id=ctx.user_id,
        event_details_json=f'{{"previousTicketScanFileId": {previous_id}, "versionNumber": {next_version}}}',
    ))
    db.commit()
    db.refresh(row)
    return {
        'ticketScanFileId': row.ticket_scan_file_id,
        'ticketId': row.ticket_id,
        'versionNumber': int(row.version_number),
        'previousTicketScanFileId': previous_id,
        'scanStatus': ticket.scan_status,
        'hasScanFile': ticket.has_scan_file,
    }


def confirm_scan_file(db: Session, ctx: SecurityContext, ticket_id: int, notes: str | None = None):
    ticket = get_ticket_or_404(db, ticket_id)
    if not can_view_ticket(ctx, ticket):
        raise PermissionError("Forbidden")

    active = db.query(TicketScanFile).filter(TicketScanFile.ticket_id == ticket_id, TicketScanFile.is_active == True).order_by(TicketScanFile.version_number.desc()).first()
    if not active:
        raise LookupError("ACTIVE_SCAN_FILE_NOT_FOUND")
    if active.is_confirmed:
        raise ValueError("SCAN_FILE_ALREADY_CONFIRMED")

    active.is_confirmed = True
    active.confirmed_by_user_id = ctx.user_id
    active.confirmed_at = datetime.utcnow()
    if notes:
        active.notes = (active.notes + '\n' if active.notes else '') + notes
    ticket.scan_status = 'FILE_CONFIRMED'
    ticket.scan_confirmed_at = active.confirmed_at
    ticket.scan_confirmed_by_user_id = ctx.user_id
    db.add(AuditEvent(
        event_type='SCAN_FILE_CONFIRMED',
        entity_name='ticket_scan_file',
        entity_id=active.ticket_scan_file_id,
        source_ticket_key=ticket.source_ticket_key,
        user_id=ctx.user_id,
        event_details_json=f'{{"versionNumber": {int(active.version_number)}}}',
    ))
    db.commit()
    return {
        'ticketScanFileId': active.ticket_scan_file_id,
        'ticketId': active.ticket_id,
        'versionNumber': int(active.version_number),
        'confirmedAt': active.confirmed_at,
        'scanStatus': ticket.scan_status,
        'hasScanFile': ticket.has_scan_file,
    }
