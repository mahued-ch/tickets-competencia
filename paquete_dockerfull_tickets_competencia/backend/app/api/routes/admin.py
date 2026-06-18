from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.security.auth import get_current_context
from app.schemas.security import SecurityContext
from app.schemas.common import ApiResponse
from app.models.user import AppUser, AppUserStore
from app.services.security_service import require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/users")
def list_users(db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        require_admin(ctx)
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    rows = db.query(AppUser).all()
    data = [{"userId": u.user_id, "loginName": u.login_name, "displayName": u.display_name, "email": u.email, "roleCode": u.role.role_code, "isActive": u.is_active} for u in rows]
    return ApiResponse.ok(data, {"count": len(data)})


@router.get("/users/{user_id}/stores")
def list_user_stores(user_id: int, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        require_admin(ctx)
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    rows = db.query(AppUserStore).filter(AppUserStore.user_id == user_id).all()
    data = [{"storeCode": r.store_code, "isActive": r.is_active} for r in rows]
    return ApiResponse.ok(data, {"count": len(data)})


@router.post("/users/{user_id}/stores")
def assign_store(user_id: int, payload: dict, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        require_admin(ctx)
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    store_code = payload.get('storeCode')
    if not store_code:
        raise HTTPException(status_code=400, detail="STORE_CODE_REQUIRED")
    row = db.query(AppUserStore).filter(AppUserStore.user_id == user_id, AppUserStore.store_code == store_code).first()
    if row:
        row.is_active = True
    else:
        row = AppUserStore(user_id=user_id, store_code=store_code, is_active=True)
        db.add(row)
    db.commit()
    return ApiResponse.ok({"userId": user_id, "storeCode": store_code, "isActive": True})
