from datetime import datetime, timezone
from typing import Optional, Dict, Any
import httpx
from app.config import get_settings
from app.utils import generate_short_code

settings = get_settings()


class SupabaseService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.SUPABASE_URL and (settings.SUPABASE_SECRET_KEY or settings.SUPABASE_KEY or settings.SUPABASE_PUBLISHABLE_KEY))

    @staticmethod
    def get_headers() -> Dict[str, str]:
        key = settings.SUPABASE_SECRET_KEY or settings.SUPABASE_KEY or settings.SUPABASE_PUBLISHABLE_KEY
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def get_url_by_short_code(cls, short_code: str) -> Optional[Dict[str, Any]]:
        url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/urls?short_code=eq.{short_code}&select=*"
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, headers=cls.get_headers())
            if res.status_code == 200:
                data = res.json()
                if data and len(data) > 0:
                    return data[0]
            return None

    @classmethod
    async def create_short_url(
        cls,
        original_url: str,
        custom_code: Optional[str] = None,
        code_length: int = 6,
        max_retries: int = 10,
    ) -> Dict[str, Any]:
        if custom_code:
            existing = await cls.get_url_by_short_code(custom_code)
            if existing:
                raise ValueError(f"Short code '{custom_code}' is already taken.")
            short_code = custom_code
        else:
            short_code = None
            for _ in range(max_retries):
                candidate = generate_short_code(code_length)
                if not await cls.get_url_by_short_code(candidate):
                    short_code = candidate
                    break
            if not short_code:
                short_code = generate_short_code(code_length + 2)

        headers = cls.get_headers()
        headers["Prefer"] = "return=representation"
        payload = {
            "original_url": original_url,
            "short_code": short_code,
            "clicks": 0,
        }

        url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/urls"
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            if res.status_code in (200, 201):
                data = res.json()
                return data[0]
            raise RuntimeError(f"Supabase error ({res.status_code}): {res.text}")

    @classmethod
    async def increment_clicks(cls, url_id: int, current_clicks: int) -> None:
        url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/urls?id=eq.{url_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.patch(
                url,
                headers=cls.get_headers(),
                json={"clicks": current_clicks + 1}
            )
