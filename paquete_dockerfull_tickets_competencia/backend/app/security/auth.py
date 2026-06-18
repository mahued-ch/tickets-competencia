from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import AppUser
from app.schemas.security import SecurityContext
from app.core.config import get_settings


settings = get_settings()


def get_current_context(
    db: Session = Depends(get_db),
    x_demo_user: str | None = Header(default=None, alias="X-Demo-User"),
):
    if not settings.demo_auth_enabled:
        raise HTTPException(status_code=401, detail="Real auth not implemented in starter")

    login_name = x_demo_user or "admin"
    user = db.query(AppUser).filter(AppUser.login_name == login_name, AppUser.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Demo user not found")

    stores = [s.store_code for s in user.stores if s.is_active]
    return SecurityContext(
        user_id=user.user_id,
        login_name=user.login_name,
        display_name=user.display_name,
        role_code=user.role.role_code,
        store_codes=stores,
    )
