import secrets
import time
from app.schemas.security import SecurityContext

_token_map: dict[str, tuple[SecurityContext, float]] = {}
TOKEN_TTL = 86400 * 7


def create_token(ctx: SecurityContext) -> str:
    token = secrets.token_hex(32)
    _token_map[token] = (ctx, time.time() + TOKEN_TTL)
    return token


def resolve_token(token: str) -> SecurityContext | None:
    entry = _token_map.get(token)
    if entry is None:
        return None
    ctx, expiry = entry
    if time.time() > expiry:
        del _token_map[token]
        return None
    return ctx


def revoke_token(token: str) -> None:
    _token_map.pop(token, None)
