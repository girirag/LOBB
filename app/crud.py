from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import URLItem
from app.utils import generate_short_code


async def get_url_by_short_code(
    db: AsyncSession, short_code: str
) -> Optional[URLItem]:
    """Fetch URL item by its short code."""
    result = await db.execute(
        select(URLItem).where(URLItem.short_code == short_code)
    )
    return result.scalar_one_or_none()


async def get_url_by_original_url(
    db: AsyncSession, original_url: str
) -> Optional[URLItem]:
    """Fetch existing URL item by original URL."""
    result = await db.execute(
        select(URLItem).where(URLItem.original_url == original_url)
    )
    return result.scalars().first()


async def create_short_url(
    db: AsyncSession,
    original_url: str,
    custom_code: Optional[str] = None,
    code_length: int = 6,
    max_retries: int = 10,
) -> URLItem:
    """Create a new shortened URL entry."""
    if custom_code:
        # Check if custom code is already in use
        existing = await get_url_by_short_code(db, custom_code)
        if existing:
            raise ValueError(f"Short code '{custom_code}' is already taken.")
        short_code = custom_code
    else:
        # Generate random unique short code
        short_code = None
        for _ in range(max_retries):
            candidate = generate_short_code(code_length)
            if not await get_url_by_short_code(db, candidate):
                short_code = candidate
                break

        if not short_code:
            # Fallback with increased length if collisions happen
            short_code = generate_short_code(code_length + 2)

    db_item = URLItem(
        original_url=original_url,
        short_code=short_code,
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


async def increment_clicks(db: AsyncSession, url_id: int) -> None:
    """Increment the click count for a URL item."""
    await db.execute(
        update(URLItem)
        .where(URLItem.id == url_id)
        .values(clicks=URLItem.clicks + 1)
    )
    await db.commit()
