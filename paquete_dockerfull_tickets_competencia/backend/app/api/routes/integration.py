from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.security import SecurityContext
from app.security.auth import get_current_context
from app.services.security_service import require_admin
from app.models.integration import IntegrationBatch, IntegrationFile, IntegrationError
from app.services.importer_service import ImporterService

router = APIRouter(prefix="/api/v1/integration", tags=["integration"])


@router.post("/import")
def run_import(db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    if ctx.role_code not in {"ADMIN", "SUPERVISOR"}:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    svc = ImporterService(db)
    results = svc.run_pending_batches()
    return ApiResponse.ok(results)


@router.get("/batches")
def list_batches(db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    if ctx.role_code not in {"ADMIN", "SUPERVISOR"}:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    rows = db.query(IntegrationBatch).order_by(IntegrationBatch.started_at.desc()).all()
    data = [{
        "batchId": r.batch_id,
        "batchCode": r.batch_code,
        "sourceSystem": r.source_system,
        "status": r.status,
        "headerRecordCount": r.header_record_count,
        "itemRecordCount": r.item_record_count,
        "storeRecordCount": r.store_record_count,
        "insertedTicketCount": r.inserted_ticket_count,
        "skippedTicketCount": r.skipped_ticket_count,
        "errorCount": r.error_count,
        "startedAt": r.started_at,
        "finishedAt": r.finished_at,
    } for r in rows]
    return ApiResponse.ok(data, {"count": len(data)})


@router.get("/batches/{batch_id}")
def get_batch(batch_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    if ctx.role_code not in {"ADMIN", "SUPERVISOR"}:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    row = db.query(IntegrationBatch).filter(IntegrationBatch.batch_id == batch_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="BATCH_NOT_FOUND")
    data = {
        "batchId": row.batch_id,
        "batchCode": row.batch_code,
        "status": row.status,
        "sourceDirectory": row.source_directory,
        "archiveDirectory": row.archive_directory,
        "errorDirectory": row.error_directory,
        "headerRecordCount": row.header_record_count,
        "itemRecordCount": row.item_record_count,
        "storeRecordCount": row.store_record_count,
        "insertedTicketCount": row.inserted_ticket_count,
        "skippedTicketCount": row.skipped_ticket_count,
        "errorCount": row.error_count,
    }
    return ApiResponse.ok(data)


@router.get("/batches/{batch_id}/files")
def get_batch_files(batch_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    if ctx.role_code not in {"ADMIN", "SUPERVISOR"}:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    rows = db.query(IntegrationFile).filter(IntegrationFile.batch_id == batch_id).all()
    data = [{"integrationFileId": r.integration_file_id, "fileType": r.file_type, "fileName": r.file_name, "recordCount": r.record_count, "status": r.status} for r in rows]
    return ApiResponse.ok(data, {"count": len(data)})


@router.get("/batches/{batch_id}/errors")
def get_batch_errors(batch_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    if ctx.role_code not in {"ADMIN", "SUPERVISOR"}:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    rows = db.query(IntegrationError).filter(IntegrationError.batch_id == batch_id).all()
    data = [{"integrationErrorId": r.integration_error_id, "entityType": r.entity_type, "sourceTicketKey": r.source_ticket_key, "errorCode": r.error_code, "errorMessage": r.error_message} for r in rows]
    return ApiResponse.ok(data, {"count": len(data)})
