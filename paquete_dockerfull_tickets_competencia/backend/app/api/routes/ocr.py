from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.security import SecurityContext
from app.security.auth import get_current_context
from app.services import ocr_service

router = APIRouter(prefix="/api/v1/tickets", tags=["ocr"])


@router.post("/{ticket_id}/ocr")
def trigger_ticket_ocr(ticket_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        data = ocr_service.trigger_ocr(db, ctx, ticket_id)
        return ApiResponse.ok(data)
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    except ValueError as ex:
        raise HTTPException(status_code=409, detail=str(ex))


@router.get("/{ticket_id}/ocr")
def get_ticket_ocr(ticket_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        data = ocr_service.get_ocr_result(db, ctx, ticket_id)
        if data is None:
            raise HTTPException(status_code=404, detail="OCR_RESULT_NOT_FOUND")
        return ApiResponse.ok(data)
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
