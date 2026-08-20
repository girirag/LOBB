# URL Shortener API (FastAPI + PostgreSQL)

A high-performance, asynchronous URL Shortener REST API built with **FastAPI**, **SQLAlchemy 2.0**, and **PostgreSQL**.

---

## Features

- 🚀 **FastAPI & Async I/O**: High-throughput asynchronous endpoints using `asyncpg`.
- 🗄️ **PostgreSQL & SQLAlchemy 2.0**: Modern async ORM mappings with full schema support.
- ✂️ **Automatic & Custom Short Codes**: Base62 collision-resistant random codes or user-defined aliases.
- 🔗 **HTTP 307 Redirects**: Seamless redirection to original URLs.
- 📊 **Analytics & Tracking**: Tracks and increments click counts for shortened links.
- 🛡️ **Pydantic v2 Validation**: Comprehensive URL structure and input sanitization.
- 🧪 **Automated Testing Suite**: Full `pytest-asyncio` coverage with isolated in-memory testing.
- 🐳 **Docker Compose Ready**: One-command PostgreSQL setup.

---

## Project Structure

```
url-shortener-api/
├── app/
│   ├── __init__.py
│   ├── config.py          # Environment settings via Pydantic Settings
│   ├── crud.py            # Database operations (create, query, click counting)
│   ├── database.py        # Async SQLAlchemy engine & session dependency
│   ├── main.py            # FastAPI endpoints and lifespan management
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic request and response schemas
│   └── utils.py           # Base62 code generator & URL helpers
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Fixtures with in-memory SQLite isolation
│   └── test_api.py        # 9+ automated tests covering all flows
├── .env.example
├── .env
├── docker-compose.yml     # PostgreSQL service
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## API Endpoints

### 1. Shorten a URL
- **Endpoint**: `POST /shorten`
- **Status Code**: `201 Created`
- **Request Body**:
```json
{
  "url": "https://en.wikipedia.org/wiki/URL_shortening",
  "custom_code": "wiki-shortener" // Optional
}
```

- **Response (201 Created)**:
```json
{
  "short_code": "wiki-shortener",
  "short_url": "http://localhost:8000/wiki-shortener",
  "original_url": "https://en.wikipedia.org/wiki/URL_shortening",
  "created_at": "2026-08-20T14:20:00Z"
}
```

---

### 2. Redirect to Original URL
- **Endpoint**: `GET /{short_code}`
- **Status Code**: `307 Temporary Redirect`
- **Behavior**: Redirects client to the original URL and increments the click counter by 1.
- **Response (404 Not Found)**: Returned if `short_code` does not exist.

---

### 3. Analytics / Stats
- **Endpoint**: `GET /stats/{short_code}`
- **Status Code**: `200 OK`
- **Response**:
```json
{
  "short_code": "wiki-shortener",
  "original_url": "https://en.wikipedia.org/wiki/URL_shortening",
  "short_url": "http://localhost:8000/wiki-shortener",
  "clicks": 42,
  "created_at": "2026-08-20T14:20:00Z"
}
```

---

### 4. Health Check
- **Endpoint**: `GET /health`
- **Response**:
```json
{
  "status": "ok",
  "database": "healthy"
}
```

---

## Quick Start & Running

### Option A: Using `uv` (Recommended)

1. **Start PostgreSQL database** (or use Docker):
   ```bash
   docker compose up -d
   ```

2. **Run the FastAPI development server**:
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```

3. **Open Interactive Swagger Documentation**:
   Visit [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

---

### Option B: Using standard Python Virtual Environment

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

## Running Automated Tests

Run the complete test suite:
```bash
uv run pytest -v
```
or with standard pytest:
```bash
pytest -v
```

---

## Example `curl` Commands

**Shorten a URL**:
```bash
curl -X POST "http://localhost:8000/shorten" \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"https://github.com/fastapi/fastapi\"}"
```

**Custom Short Code**:
```bash
curl -X POST "http://localhost:8000/shorten" \
     -H "Content-Type: application/json" \
     -d "{\"url\": \"https://github.com/fastapi/fastapi\", \"custom_code\": \"fastapi\"}"
```

**Access & Redirect**:
```bash
curl -i "http://localhost:8000/fastapi"
```

**Check Click Analytics**:
```bash
curl "http://localhost:8000/stats/fastapi"
```
