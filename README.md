# MARKET PULSE
> A watchlist that watches for you.

## Overview

Market Pulse is an intelligent stock watchlist application that automatically detects meaningful market changes based on user preferences. It provides real-time alerts and attention prioritization powered by a custom Pulse Engine (0–100 score).

## Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | FastAPI + SQLAlchemy + WebSockets |
| Auth | Google OAuth → signed JWT (HS256, `python-jose`) |
| Background jobs | ARQ + Redis |
| Intelligence | Custom Pulse Engine + ChangeDetector |

---

## Local Development

### Backend

```bash
cd backend
python -m venv venv

# Activate venv
.\\venv\\Scripts\\activate          # Windows PowerShell
source venv/bin/activate            # macOS / Linux

pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — minimum required: JWT_SECRET (any random string for local dev)
# For local dev you can also set DEV_TRUST_HEADER=1 to skip JWT and use X-User-Id headers

uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

> **SQLite fallback**: If `DATABASE_URL` is not set (or points to SQLite), the app
> uses `backend/sql_app.db` automatically. No PostgreSQL required for local dev.

### Frontend

```bash
cd frontend
npm install

# Optional: create .env.local to override API base
# echo "VITE_API_BASE=http://localhost:8000" > .env.local

npm run dev
# → http://localhost:5173
```

### Running Tests

```bash
cd backend
.\\venv\\Scripts\\activate
pytest tests/ -v
```

---

## Deployment

### Backend (Render)

A `render.yaml` Blueprint is included at the repo root. It provisions:
- **Web service** — FastAPI app on Python 3.11
- **PostgreSQL** — managed Render database
- **Redis** — managed Render Redis (for ARQ workers and WebSocket pub/sub)

**Steps:**
1. Push this repo to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com) → **New → Blueprint**.
3. Connect your GitHub repo — Render auto-detects `render.yaml`.
4. Review the generated services, then click **Apply**.
5. After deploy, copy the backend URL (e.g. `https://market-pulse-api.onrender.com`).
6. Update `FRONTEND_URL` in the Render dashboard to your Vercel URL once deployed.

**Environment variables set automatically by Blueprint:**
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `JWT_EXPIRE_MINUTES`
- `DEV_TRUST_HEADER`

> [!CAUTION]
> Make sure `DEV_TRUST_HEADER` is set to `0` in production to enforce JWT validation.

---

### Frontend (Vercel)

A `frontend/vercel.json` is included to handle single-page application routing and API configuration.

**Steps:**
1. Go to [Vercel Dashboard](https://vercel.com/new) → **Import Git Repository**.
2. Set **Root Directory** to `frontend`.
3. Add environment variables in the Vercel dashboard:
   - `VITE_API_BASE`: Set this to your Render backend URL (e.g., `https://market-pulse-api.onrender.com`). The `api.ts` service uses this to route API requests dynamically.
   - `VITE_GOOGLE_CLIENT_ID`: Your Google OAuth 2.0 Client ID.
4. Click **Deploy**.

> **Note**: `npm run build` will execute on Vercel automatically and compile the Vite app using the provided `.env` variables.

---

## Google OAuth Setup

1. Go to [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
2. Create an OAuth 2.0 Client ID (Web application)
3. Under "Authorized JavaScript origins" add every URL the app is served from (`http://localhost:5173` for dev, and the production/Vercel URL)
4. Paste that client ID into `frontend/.env` as `VITE_GOOGLE_CLIENT_ID`

---

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///./sql_app.db` | SQLAlchemy DB connection string |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis for ARQ and WebSocket pub/sub |
| `JWT_SECRET` | **Yes (prod)** | `dev-insecure-secret-change-in-prod` | HS256 signing secret — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_EXPIRE_MINUTES` | No | `10080` (7 days) | Token lifetime |
| `DEV_TRUST_HEADER` | No | `0` | Set to `1` for local dev to skip JWT and use `X-User-Id` header |
| `FRONTEND_URL` | No | `http://localhost:5173` | Allowed CORS origin |
| `MARKET_API_URL` | No | `mock` | Market data provider URL |
| `MARKET_API_KEY` | No | `mock` | Market data API key |

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE` | `http://localhost:8000` | Backend URL |
| `VITE_GOOGLE_CLIENT_ID` | — | Google OAuth 2.0 Client ID |

---

## Demo Flow

1. Open the dashboard.
2. Click **"Simulate Market Change"** — triggers a synthetic price spike.
3. Observe the Pulse Score jump in real-time via WebSocket.
4. Check **Notifications** — a threshold-crossing alert appears.
5. Toggle **Smart Watch** settings to tune your personal thresholds.
