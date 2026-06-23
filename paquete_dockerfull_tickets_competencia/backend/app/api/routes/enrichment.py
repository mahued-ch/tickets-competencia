from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.enrichment import EnrichmentConfirmRequest, EnrichmentRejectRequest, EnrichmentItemUpdate
from app.schemas.security import SecurityContext
from app.security.auth import get_current_context
from app.services import enrichment_service

router = APIRouter(prefix="/api/v1/tickets", tags=["enrichment"])


@router.post("/{ticket_id}/enrichment")
def trigger_enrichment(ticket_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        data = enrichment_service.run_enrichment(db, ctx, ticket_id)
        return ApiResponse.ok(data)
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    except ValueError as ex:
        raise HTTPException(status_code=409, detail=str(ex))


@router.get("/{ticket_id}/enrichment-preview")
def get_enrichment_preview(ticket_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        data = enrichment_service.get_enrichment_preview(db, ctx, ticket_id)
        if data is None:
            raise HTTPException(status_code=404, detail="ENRICHMENT_NOT_FOUND")
        return ApiResponse.ok(data)
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")


@router.put("/{ticket_id}/enrichment-items")
def update_enrichment_items(ticket_id: int, payload: list[EnrichmentItemUpdate], db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        items = [m.model_dump() for m in payload]
        data = enrichment_service.update_enrichment_items(db, ctx, ticket_id, items)
        return ApiResponse.ok(data)
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    except ValueError as ex:
        raise HTTPException(status_code=409, detail=str(ex))


@router.post("/{ticket_id}/enrichment-confirm")
def confirm_enrichment(ticket_id: int, payload: EnrichmentConfirmRequest | None = None, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        items = [m.model_dump() for m in payload.items] if payload and payload.items else None
        data = enrichment_service.confirm_enrichment(db, ctx, ticket_id, payload.notes if payload else None, items)
        return ApiResponse.ok(data)
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    except ValueError as ex:
        raise HTTPException(status_code=409, detail=str(ex))


@router.post("/{ticket_id}/enrichment-reject")
def reject_enrichment(ticket_id: int, payload: EnrichmentRejectRequest | None = None, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        data = enrichment_service.reject_enrichment(db, ctx, ticket_id, payload.notes if payload else None)
        return ApiResponse.ok(data)
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    except ValueError as ex:
        raise HTTPException(status_code=409, detail=str(ex))
