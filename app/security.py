"""Hash de contraseñas con PBKDF2-SHA256 (biblioteca estándar de Python)."""
import hashlib
import hmac
import secrets

ITER = 200_000


def hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), ITER).hex()
    return f"pbkdf2${ITER}${salt}${digest}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, it, salt, digest = stored.split("$")
    except ValueError:
        return False
    test = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), int(it)).hex()
    return hmac.compare_digest(test, digest)
