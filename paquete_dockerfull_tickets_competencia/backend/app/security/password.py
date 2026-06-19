import hashlib
import secrets
import base64

ALGORITHM = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), DEFAULT_ITERATIONS
    )
    digest = base64.b64encode(dk).decode("utf-8")
    return f"{ALGORITHM}${DEFAULT_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        parts = stored.split("$")
        if len(parts) != 4:
            return False
        _alg, iterations_str, salt, digest = parts
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations_str)
        )
        return base64.b64encode(dk).decode("utf-8") == digest
    except (ValueError, IndexError):
        return False
