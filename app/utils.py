import secrets
import string

BASE62_ALPHABET = string.ascii_letters + string.digits  # 62 characters: a-z, A-Z, 0-9


def generate_short_code(length: int = 6) -> str:
    """Generate a secure, random base62 string of specified length."""
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


def build_short_url(base_url: str, short_code: str) -> str:
    """Construct full shortened URL using base URL and short code."""
    base = base_url.rstrip("/")
    return f"{base}/{short_code}"
