from typing import Any
from pydantic import BaseModel, Field


class ApiError(BaseModel):
    code: str
    message: str
    field: str | None = None
    details: dict[str, Any] | None = None


class ApiResponse(BaseModel):
    success: bool = True
    data: Any = None
    meta: dict[str, Any] | None = None
    errors: list[ApiError] = Field(default_factory=list)

    @classmethod
    def ok(cls, data: Any = None, meta: dict[str, Any] | None = None):
        return cls(success=True, data=data, meta=meta, errors=[])

    @classmethod
    def fail(cls, code: str, message: str, status_details: dict[str, Any] | None = None):
        return cls(success=False, data=None, meta=None, errors=[ApiError(code=code, message=message, details=status_details)])
