from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.security.auth import get_current_context
from app.schemas.security import SecurityContext
from app.services import audit_service

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/events")
def list_audit_events(
    eventType: str | None = None,
    entityName: str | None = None,
    sourceTicketKey: str | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    ctx: SecurityContext = Depends(get_current_context),
):
    if ctx.role_code not in {"ADMIN", "SUPERVISOR"}:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    items, meta = audit_service.search_events(db, ctx, {
        "eventType": eventType,
        "entityName": entityName,
        "sourceTicketKey": sourceTicketKey,
        "dateFrom": dateFrom,
        "dateTo": dateTo,
        "page": page,
        "pageSize": pageSize,
    })
    return ApiResponse.ok(items, meta)
