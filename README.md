# URL Shortener (ZipLink) — Full Stack

A high-performance, full-stack URL Shortener built with **FastAPI & PostgreSQL** (Backend) and **React & Vite** (Frontend), architected for **Render.com + Vercel** deployment.

---

## Project Structure

```
├── backend/                  # FastAPI + PostgreSQL / Supabase
│   ├── app/
│   │   ├── config.py         # App configuration & environment parsing
│   │   ├── crud.py           # Database operations
│   │   ├── database.py       # Async SQLAlchemy engine & session management
│   │   ├── main.py           # FastAPI routes & CORS middleware
│   │   ├── models.py         # SQLAlchemy URL model
│   │   ├── schemas.py        # Pydantic request/response validation
│   │   ├── supabase_service.py # Direct Supabase HTTPS client
│   │   └── utils.py          # Base62 code generator
│   ├── tests/                # Automated test suite (10/10 tests passing)
│   ├── Dockerfile            # Container deployment
│   ├── render.yaml           # Render.com Blueprint
│   ├── requirements.txt      # Python dependencies
│   └── .env.example
│
├── frontend/                 # React 18 + Vite Web Application
│   ├── src/
│   │   ├── App.jsx           # Main UI (Shorten, Copy, Analytics, Recents)
│   │   ├── index.css         # Modern Dark Glassmorphism Styling
│   │   └── main.jsx
│   ├── package.json
│   ├── vercel.json           # Vercel SPA routing
│   ├── vite.config.js
│   └── .env.example
│
└── README.md
```

---

## 🚀 Deployment Guide (Render + Vercel)

### Part 1: Deploy Backend to Render.com (2 minutes)

1. Go to **[Render Dashboard](https://dashboard.render.com/)** and click **New +** → **Web Service**.
2. Connect your GitHub repository (`girirag/LOBB`).
3. Set the following configuration:
   - **Name**: `url-shortener-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add your Database Environment Variable in **Environment Variables**:
   - `DATABASE_URL`: `postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.apdlqeorlszyqyppawwl.supabase.co:5432/postgres`
   - *(Optional for Supabase HTTPS)*: `SUPABASE_URL` and `SUPABASE_SECRET_KEY`
5. Click **Create Web Service**.
6. Copy your Render URL when deployed (e.g. `https://url-shortener-backend-xxxx.onrender.com`).

---

### Part 2: Deploy Frontend to Vercel (1 minute)

1. Go to **[Vercel Dashboard](https://vercel.com/new)** and click **"Add New Project"** → **Import** your repository (`girirag/LOBB`).
2. In the project setup:
   - **Root Directory**: Click *Edit* and select **`frontend`**.
   - **Framework Preset**: `Vite` (auto-detected).
3. Under **Environment Variables**, add:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: Your Render Backend URL from Part 1 (e.g. `https://url-shortener-backend-xxxx.onrender.com`).
4. Click **Deploy**.

---

## 💻 Local Development

### Run Backend
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

### Run Frontend
```bash
cd frontend
npm install
npm run dev
```
- Web UI: `http://localhost:3000`

---

## 🧪 Running Tests

```bash
cd backend
uv run pytest -v
```
All 10 unit and integration tests covering URL shortening, collision avoidance, 307 redirects, 404s, and analytics pass out-of-the-box.
