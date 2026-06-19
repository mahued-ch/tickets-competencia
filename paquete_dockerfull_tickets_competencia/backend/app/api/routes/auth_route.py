from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.models.user import AppUser
from app.security.password import verify_password
from app.security.token_store import create_token
from app.security.auth import get_current_context
from app.schemas.security import SecurityContext

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    login_name: str
    password: str


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AppUser).filter(
        AppUser.login_name == body.login_name,
        AppUser.is_active == True
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")
    if not user.password_hash:
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")

    stores = [s.store_code for s in user.stores if s.is_active]
    ctx = SecurityContext(
        user_id=user.user_id,
        login_name=user.login_name,
        display_name=user.display_name,
        role_code=user.role.role_code,
        store_codes=stores,
    )
    token = create_token(ctx)
    return ApiResponse.ok({
        "token": token,
        "userId": user.user_id,
        "loginName": user.login_name,
        "displayName": user.display_name,
        "roleCode": user.role.role_code,
        "storeCodes": stores,
    })


class LogoutRequest(BaseModel):
    token: str


@router.post("/logout")
def logout(body: LogoutRequest):
    from app.security.token_store import revoke_token
    revoke_token(body.token)
    return ApiResponse.ok({"message": "Logged out"})


@router.get("/verify")
def verify_token(ctx: SecurityContext = Depends(get_current_context)):
    return ApiResponse.ok({
        "userId": ctx.user_id,
        "loginName": ctx.login_name,
        "displayName": ctx.display_name,
        "roleCode": ctx.role_code,
        "storeCodes": ctx.store_codes,
    })


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.put("/password")
def change_own_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Depends(get_current_context),
):
    user = db.query(AppUser).filter(AppUser.user_id == ctx.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    if not user.password_hash or not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="CURRENT_PASSWORD_MISMATCH")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="PASSWORD_TOO_SHORT")
    from app.security.password import hash_password
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return ApiResponse.ok({"message": "Password updated"})
