from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc
from app.models.ticket import AuditEvent
from app.models.user import AppUser
from app.schemas.security import SecurityContext


def _row_to_dto(row) -> dict:
    return {
        "auditEventId": row.audit_event_id,
        "eventType": row.event_type,
        "entityName": row.entity_name,
        "entityId": row.entity_id,
        "sourceTicketKey": row.source_ticket_key,
        "userId": row.user_id,
        "userDisplayName": row.user.display_name if row.user else None,
        "eventTimestamp": row.event_timestamp,
        "ipAddress": row.ip_address,
        "eventDetails": row.event_details_json,
    }


def search_events(db: Session, ctx: SecurityContext, filters: dict) -> tuple[list[dict], dict]:
    if ctx.role_code not in {"ADMIN", "SUPERVISOR"}:
        raise PermissionError("Only ADMIN/SUPERVISOR can view audit events")

    query = db.query(AuditEvent).options(joinedload(AuditEvent.user))

    if value := filters.get("eventType"):
        query = query.filter(AuditEvent.event_type == value)
    if value := filters.get("entityName"):
        query = query.filter(AuditEvent.entity_name == value)
    if value := filters.get("sourceTicketKey"):
        query = query.filter(AuditEvent.source_ticket_key == value)
    if value := filters.get("dateFrom"):
        query = query.filter(AuditEvent.event_timestamp >= value)
    if value := filters.get("dateTo"):
        query = query.filter(AuditEvent.event_timestamp <= value)

    total = query.count()
    page = int(filters.get("page", 1))
    page_size = int(filters.get("pageSize", 50))
    page_size = min(page_size, 200)
    offset = (page - 1) * page_size

    rows = query.order_by(AuditEvent.event_timestamp.desc()).offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if page_size else 1

    return [_row_to_dto(r) for r in rows], {
        "page": page,
        "pageSize": page_size,
        "totalRecords": total,
        "totalPages": total_pages,
    }
