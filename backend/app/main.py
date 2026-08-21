from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import get_settings, Settings
from app.database import get_db, init_db
from app.schemas import ShortenRequest, ShortenResponse, StatsResponse, HealthResponse
from app.utils import build_short_url
from app.supabase_service import SupabaseService
import app.crud as crud

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="High-performance URL shortener backend API with PostgreSQL and Supabase support.",
    version="1.0.0",
)

# Enable CORS for Frontend (Vercel, localhost, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint to verify API and database connectivity."""
    if SupabaseService.is_configured():
        return HealthResponse(status="ok", database="supabase (https)")

    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    return HealthResponse(status="ok", database=db_status)


@app.post(
    "/shorten",
    response_model=ShortenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["URLs"],
    summary="Shorten a long URL",
)
async def shorten_url(
    payload: ShortenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    app_settings: Settings = Depends(get_settings),
):
    """
    Accepts a long URL and generates or assigns a unique short code.
    Returns the shortened URL metadata.
    """
    original_url_str = str(payload.url)
    base_url = app_settings.BASE_URL or str(request.base_url).rstrip("/")

    # Supabase HTTPS client fallback
    if SupabaseService.is_configured():
        try:
            item = await SupabaseService.create_short_url(
                original_url=original_url_str,
                custom_code=payload.custom_code,
                code_length=app_settings.SHORT_CODE_LENGTH,
            )
            return ShortenResponse(
                short_code=item["short_code"],
                short_url=build_short_url(base_url, item["short_code"]),
                original_url=item["original_url"],
                created_at=item["created_at"],
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Standard PostgreSQL / SQLite via SQLAlchemy
    try:
        url_item = await crud.create_short_url(
            db=db,
            original_url=original_url_str,
            custom_code=payload.custom_code,
            code_length=app_settings.SHORT_CODE_LENGTH,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    short_url = build_short_url(base_url, url_item.short_code)

    return ShortenResponse(
        short_code=url_item.short_code,
        short_url=short_url,
        original_url=url_item.original_url,
        created_at=url_item.created_at,
    )


@app.get(
    "/stats/{short_code}",
    response_model=StatsResponse,
    tags=["URLs"],
    summary="Get analytics for a shortened URL",
)
async def get_url_stats(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    app_settings: Settings = Depends(get_settings),
):
    """Fetch click count and metadata for a specific short code."""
    base_url = app_settings.BASE_URL or str(request.base_url).rstrip("/")

    if SupabaseService.is_configured():
        item = await SupabaseService.get_url_by_short_code(short_code)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Short URL with code '{short_code}' not found.",
            )
        return StatsResponse(
            short_code=item["short_code"],
            original_url=item["original_url"],
            short_url=build_short_url(base_url, item["short_code"]),
            clicks=item.get("clicks", 0),
            created_at=item["created_at"],
        )

    url_item = await crud.get_url_by_short_code(db, short_code)
    if not url_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short URL with code '{short_code}' not found.",
        )

    short_url = build_short_url(base_url, url_item.short_code)

    return StatsResponse(
        short_code=url_item.short_code,
        original_url=url_item.original_url,
        short_url=short_url,
        clicks=url_item.clicks,
        created_at=url_item.created_at,
    )


@app.get(
    "/{short_code}",
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    tags=["URLs"],
    summary="Redirect to original URL",
)
async def redirect_to_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Redirects the client to the original long URL associated with the short code.
    Increments the access click counter.
    """
    if SupabaseService.is_configured():
        item = await SupabaseService.get_url_by_short_code(short_code)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Short URL with code '{short_code}' not found.",
            )
        await SupabaseService.increment_clicks(item["id"], item.get("clicks", 0))
        return RedirectResponse(
            url=item["original_url"],
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    url_item = await crud.get_url_by_short_code(db, short_code)
    if not url_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short URL with code '{short_code}' not found.",
        )

    # Increment click count
    await crud.increment_clicks(db, url_item.id)

    return RedirectResponse(
        url=url_item.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
