from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import get_settings, Settings
from app.database import get_db, init_db
from app.schemas import ShortenRequest, ShortenResponse, StatsResponse, HealthResponse
from app.utils import build_short_url
from app.supabase_service import SupabaseService
import app.crud as crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist safely
    try:
        await init_db()
    except Exception as e:
        import logging
        logging.warning(f"Database init warning: {e}")
    yield
    # Shutdown: clean up if necessary


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="A high-performance URL shortener API built with FastAPI and PostgreSQL.",
    version="1.0.0",
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/", response_class=HTMLResponse, tags=["Web UI"], summary="URL Shortener Home Page")
async def home_page():
    """Interactive Web UI to shorten and test URLs directly in browser."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>URL Shortener</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, sans-serif; }
            body {
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #f8fafc;
                padding: 20px;
            }
            .card {
                background: rgba(30, 41, 59, 0.85);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 40px;
                width: 100%;
                max-width: 560px;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }
            .header { text-align: center; margin-bottom: 28px; }
            .badge {
                display: inline-block;
                background: rgba(99, 102, 241, 0.2);
                color: #818cf8;
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 0.8rem;
                font-weight: 600;
                margin-bottom: 12px;
                border: 1px solid rgba(99, 102, 241, 0.3);
            }
            h1 { font-size: 1.85rem; font-weight: 700; color: #fff; margin-bottom: 8px; }
            p.subtitle { color: #94a3b8; font-size: 0.95rem; }
            .form-group { margin-bottom: 18px; }
            label { display: block; font-size: 0.875rem; font-weight: 500; color: #cbd5e1; margin-bottom: 6px; }
            input {
                width: 100%;
                padding: 12px 16px;
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 10px;
                color: #fff;
                font-size: 0.95rem;
                outline: none;
                transition: border-color 0.2s;
            }
            input:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2); }
            button {
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                color: #fff;
                border: none;
                border-radius: 10px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.1s, opacity 0.2s;
                margin-top: 10px;
            }
            button:hover { opacity: 0.95; transform: translateY(-1px); }
            button:active { transform: translateY(0); }
            .result-box {
                display: none;
                margin-top: 24px;
                background: rgba(15, 23, 42, 0.8);
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 18px;
            }
            .result-box.show { display: block; animation: fadeIn 0.3s ease; }
            .result-header { font-size: 0.8rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
            .short-link-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
            .short-link {
                color: #38bdf8;
                font-weight: 600;
                text-decoration: none;
                word-break: break-all;
            }
            .short-link:hover { text-decoration: underline; }
            .copy-btn {
                width: auto;
                margin: 0;
                padding: 8px 14px;
                font-size: 0.85rem;
                background: #334155;
                color: #e2e8f0;
            }
            .copy-btn:hover { background: #475569; }
            .error-box {
                display: none;
                margin-top: 18px;
                background: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.3);
                color: #f87171;
                padding: 12px 16px;
                border-radius: 10px;
                font-size: 0.9rem;
            }
            .error-box.show { display: block; }
            .footer-links {
                margin-top: 24px;
                text-align: center;
                font-size: 0.85rem;
                color: #64748b;
            }
            .footer-links a { color: #818cf8; text-decoration: none; margin: 0 8px; }
            .footer-links a:hover { text-decoration: underline; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <span class="badge">FastAPI + PostgreSQL</span>
                <h1>URL Shortener</h1>
                <p class="subtitle">Enter a long URL to generate a fast, shortened link</p>
            </div>
            
            <form id="shortenForm" onsubmit="handleShorten(event)">
                <div class="form-group">
                    <label for="urlInput">Destination Long URL</label>
                    <input type="url" id="urlInput" placeholder="https://example.com/very/long/url" required />
                </div>
                
                <div class="form-group">
                    <label for="customCodeInput">Custom Alias (Optional)</label>
                    <input type="text" id="customCodeInput" placeholder="e.g. my-custom-link" pattern="[a-zA-Z0-9_-]{3,32}" title="3-32 alphanumeric characters, dashes, or underscores" />
                </div>
                
                <button type="submit" id="submitBtn">Shorten URL</button>
            </form>

            <div id="errorBox" class="error-box"></div>

            <div id="resultBox" class="result-box">
                <div class="result-header">Your Shortened Link</div>
                <div class="short-link-row">
                    <a id="shortUrlLink" class="short-link" href="#" target="_blank"></a>
                    <button type="button" class="copy-btn" onclick="copyLink()">Copy</button>
                </div>
            </div>

            <div class="footer-links">
                <a href="/docs" target="_blank">Interactive Swagger Docs</a> • 
                <a href="/redoc" target="_blank">ReDoc</a> • 
                <a href="/health" target="_blank">Health</a>
            </div>
        </div>

        <script>
            async function handleShorten(e) {
                e.preventDefault();
                const url = document.getElementById('urlInput').value.trim();
                const customCode = document.getElementById('customCodeInput').value.trim();
                const errorBox = document.getElementById('errorBox');
                const resultBox = document.getElementById('resultBox');
                const submitBtn = document.getElementById('submitBtn');

                errorBox.classList.remove('show');
                resultBox.classList.remove('show');
                submitBtn.disabled = true;
                submitBtn.innerText = 'Shortening...';

                try {
                    const payload = { url: url };
                    if (customCode) payload.custom_code = customCode;

                    const res = await fetch('/shorten', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    const data = await res.json();
                    if (!res.ok) {
                        const errMsg = data.detail ? (Array.isArray(data.detail) ? data.detail[0].msg : data.detail) : 'Failed to shorten URL';
                        throw new Error(errMsg);
                    }

                    const shortUrlLink = document.getElementById('shortUrlLink');
                    shortUrlLink.href = data.short_url;
                    shortUrlLink.innerText = data.short_url;
                    resultBox.classList.add('show');
                } catch (err) {
                    errorBox.innerText = err.message;
                    errorBox.classList.add('show');
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.innerText = 'Shorten URL';
                }
            }

            function copyLink() {
                const link = document.getElementById('shortUrlLink').innerText;
                navigator.clipboard.writeText(link).then(() => {
                    const btn = document.querySelector('.copy-btn');
                    btn.innerText = 'Copied!';
                    setTimeout(() => { btn.innerText = 'Copy'; }, 2000);
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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

    # If Supabase credentials are configured, use pure HTTPS PostgREST client
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

    # Otherwise fallback to local SQLAlchemy
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
