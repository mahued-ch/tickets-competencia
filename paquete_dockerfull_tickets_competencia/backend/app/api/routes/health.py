from fastapi import APIRouter
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health():
    return ApiResponse.ok({"status": "ok"})
