from pydantic import BaseModel


class SecurityContext(BaseModel):
    user_id: int
    login_name: str
    display_name: str
    role_code: str
    store_codes: list[str]
