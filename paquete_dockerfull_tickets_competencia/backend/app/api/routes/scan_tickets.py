from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.security import SecurityContext
from app.security.auth import get_current_context
from app.services import scan_ticket_service

settings = get_settings()
router = APIRouter(prefix="/api/v1/scan-tickets", tags=["scan-tickets"])


@router.post("")
async def create_scan_ticket(
    file: UploadFile = File(...),
    business_code: str = Form(...),
    store_code: str = Form(...),
    db: Session = Depends(get_db),
    ctx: SecurityContext = Depends(get_current_context),
):
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if ext not in settings.allowed_extensions_list:
        raise HTTPException(status_code=400, detail="INVALID_FILE_TYPE")
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="INVALID_FILE_SIZE")

    try:
        data = scan_ticket_service.create_ticket_from_scan(
            db, ctx, content, file.filename, business_code, store_code,
        )
        return ApiResponse.ok(data)
    except ValueError as ex:
        raise HTTPException(status_code=409, detail=str(ex))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@router.get("")
def list_scan_tickets(
    business_code: str | None = Query(default=None),
    store_code: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    db: Session = Depends(get_db),
    ctx: SecurityContext = Depends(get_current_context),
):
    filters = {
        "sourceBusinessCode": business_code,
        "sourceStoreCode": store_code,
        "sourceTicketDateFrom": date_from,
        "sourceTicketDateTo": date_to,
        "page": page,
        "pageSize": page_size,
    }
    data, meta = scan_ticket_service.list_scan_tickets(db, ctx, filters)
    return ApiResponse.ok(data, meta)


@router.get("/{ticket_id}")
def get_scan_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Depends(get_current_context),
):
    try:
        data = scan_ticket_service.get_scan_ticket_detail(db, ctx, ticket_id)
        if data is None:
            raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
        return ApiResponse.ok(data)
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")


@router.put("/{ticket_id}/items")
def update_scan_ticket_items(
    ticket_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Depends(get_current_context),
):
    try:
        items = payload.get("items", [])
        business_code = payload.get("businessCode")
        store_code = payload.get("storeCode")
        data = scan_ticket_service.update_scan_ticket_items(
            db, ctx, ticket_id, items, business_code, store_code,
        )
        return ApiResponse.ok(data)
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    except ValueError as ex:
        raise HTTPException(status_code=409, detail=str(ex))


@router.post("/{ticket_id}/finalize")
def finalize_scan_ticket(
    ticket_id: int,
    payload: dict | None = None,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Depends(get_current_context),
):
    try:
        items = payload.get("items") if payload else None
        business_code = payload.get("businessCode") if payload else None
        store_code = payload.get("storeCode") if payload else None
        data = scan_ticket_service.finalize_scan_ticket(
            db, ctx, ticket_id, items, business_code, store_code,
        )
        return ApiResponse.ok(data)
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    except ValueError as ex:
        raise HTTPException(status_code=409, detail=str(ex))
