from fastapi import APIRouter, Depends
from app.schemas.common import ApiResponse
from app.security.auth import get_current_context
from app.schemas.security import SecurityContext

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.get("/me")
def me(ctx: SecurityContext = Depends(get_current_context)):
    return ApiResponse.ok({
        "userId": ctx.user_id,
        "loginName": ctx.login_name,
        "displayName": ctx.display_name,
        "roleCode": ctx.role_code,
        "storeCodes": ctx.store_codes,
    })
