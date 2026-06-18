from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.security.auth import get_current_context
from app.schemas.security import SecurityContext
from app.services import ticket_service

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])


@router.get("")
def search_tickets(
    sourceTicketKey: str | None = None,
    sourceStatusCode: str | None = None,
    scanStatus: str | None = None,
    sourceTicketDateFrom: str | None = None,
    sourceTicketDateTo: str | None = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    ctx: SecurityContext = Depends(get_current_context),
):
    items, meta = ticket_service.search_tickets(db, ctx, {
        'sourceTicketKey': sourceTicketKey,
        'sourceStatusCode': sourceStatusCode,
        'scanStatus': scanStatus,
        'sourceTicketDateFrom': sourceTicketDateFrom,
        'sourceTicketDateTo': sourceTicketDateTo,
        'page': page,
        'pageSize': pageSize,
    })
    return ApiResponse.ok(items, meta)


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        data = ticket_service.get_ticket_detail(db, ctx, ticket_id)
        return ApiResponse.ok(data)
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")


@router.get("/{ticket_id}/items")
def get_ticket_items(ticket_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        data = ticket_service.get_ticket_items(db, ctx, ticket_id)
        return ApiResponse.ok(data, {"count": len(data)})
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")


@router.get("/{ticket_id}/stores")
def get_ticket_stores(ticket_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        data = ticket_service.get_ticket_stores(db, ctx, ticket_id)
        return ApiResponse.ok(data, {"count": len(data)})
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
