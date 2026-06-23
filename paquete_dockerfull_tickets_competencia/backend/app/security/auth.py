from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import AppUser
from app.schemas.security import SecurityContext
from app.core.config import get_settings
from app.security.token_store import resolve_token


settings = get_settings()


def get_current_context(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_demo_user: str | None = Header(default=None, alias="X-Demo-User"),
    token_query: str | None = Query(default=None, alias="token"),
):
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):]
    if not token and token_query:
        token = token_query

    if token:
        ctx = resolve_token(token)
        if ctx:
            return ctx
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")

    if settings.demo_auth_enabled and x_demo_user:
        user = db.query(AppUser).filter(AppUser.login_name == x_demo_user, AppUser.is_active == True).first()
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

    raise HTTPException(status_code=401, detail="UNAUTHORIZED")
