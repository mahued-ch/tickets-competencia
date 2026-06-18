from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.security import SecurityContext
from app.security.auth import get_current_context
from app.services import ticket_service
from app.services.scan_file_service import upload_or_replace_scan_file, confirm_scan_file
from app.storage.local_storage import LocalStorageService

settings = get_settings()
router = APIRouter(prefix="/api/v1/tickets", tags=["scan-file"])
storage = LocalStorageService()


@router.get("/{ticket_id}/scan-file")
def get_active_scan_file(ticket_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        data = ticket_service.get_active_scan_file(db, ctx, ticket_id)
        return ApiResponse.ok(data)
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")


@router.post("/{ticket_id}/scan-file")
async def upload_scan_file(
    ticket_id: int,
    file: UploadFile = File(...),
    notes: str | None = Form(default=None),
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
        stored = storage.save_ticket_file(ticket_id=ticket_id, original_name=file.filename, content=content)
        data = upload_or_replace_scan_file(db, ctx, ticket_id, stored, notes)
        return ApiResponse.ok(data)
    except LookupError:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    except ValueError as ex:
        raise HTTPException(status_code=409, detail=str(ex))


@router.put("/{ticket_id}/scan-file/confirm")
def confirm_active_scan_file(ticket_id: int, payload: dict | None = None, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    notes = payload.get('notes') if payload else None
    try:
        data = confirm_scan_file(db, ctx, ticket_id, notes)
        return ApiResponse.ok(data)
    except LookupError as ex:
        status = 404 if str(ex) == 'TICKET_NOT_FOUND' else 409
        raise HTTPException(status_code=status, detail=str(ex))
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    except ValueError as ex:
        raise HTTPException(status_code=409, detail=str(ex))


@router.get("/{ticket_id}/scan-file/content")
def stream_scan_file(ticket_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        active = ticket_service.get_active_scan_file(db, ctx, ticket_id)
        if not active:
            raise HTTPException(status_code=404, detail="SCAN_FILE_NOT_FOUND")
        content = storage.open_read(active.storagePath)
        return Response(content=content, media_type=active.mimeType, headers={"Content-Disposition": f'inline; filename="{active.fileName}"'})
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
