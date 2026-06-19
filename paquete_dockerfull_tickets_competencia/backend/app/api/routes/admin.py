from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.security.auth import get_current_context
from app.schemas.security import SecurityContext
from app.schemas.common import ApiResponse
from app.models.user import AppRole, AppUser, AppUserStore
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


class AdminSetPasswordRequest(BaseModel):
    new_password: str


class CreateUserRequest(BaseModel):
    login_name: str
    display_name: str
    password: str
    role_code: str = "STORE_USER"
    email: str | None = None


@router.post("/users")
def create_user(
    body: CreateUserRequest,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Depends(get_current_context),
):
    try:
        require_admin(ctx)
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="PASSWORD_TOO_SHORT")
    existing = db.query(AppUser).filter(AppUser.login_name == body.login_name).first()
    if existing:
        raise HTTPException(status_code=409, detail="LOGIN_NAME_ALREADY_EXISTS")
    role = db.query(AppRole).filter(AppRole.role_code == body.role_code).first()
    if not role:
        raise HTTPException(status_code=400, detail="INVALID_ROLE_CODE")
    from app.security.password import hash_password
    user = AppUser(
        login_name=body.login_name,
        display_name=body.display_name,
        email=body.email,
        password_hash=hash_password(body.password),
        role_id=role.role_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ApiResponse.ok({
        "userId": user.user_id,
        "loginName": user.login_name,
        "displayName": user.display_name,
        "email": user.email,
        "roleCode": user.role.role_code,
        "isActive": user.is_active,
    })


@router.put("/users/{user_id}/password")
def admin_set_password(
    user_id: int,
    body: AdminSetPasswordRequest,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Depends(get_current_context),
):
    try:
        require_admin(ctx)
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    user = db.query(AppUser).filter(AppUser.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="PASSWORD_TOO_SHORT")
    from app.security.password import hash_password
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return ApiResponse.ok({"message": "Password updated for user"})


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


@router.delete("/users/{user_id}/stores/{store_code}")
def remove_store(user_id: int, store_code: str, db: Session = Depends(get_db), ctx: SecurityContext = Depends(get_current_context)):
    try:
        require_admin(ctx)
    except PermissionError:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    row = db.query(AppUserStore).filter(AppUserStore.user_id == user_id, AppUserStore.store_code == store_code).first()
    if not row:
        raise HTTPException(status_code=404, detail="STORE_NOT_FOUND")
    db.delete(row)
    db.commit()
    return ApiResponse.ok({"message": "Store removed"})
