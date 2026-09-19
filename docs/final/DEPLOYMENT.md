# PostCare Production Deployment Guide

*(For the complete submission documentation index, visit [`docs/final/INDEX.md`](./INDEX.md) and [`DEPLOYMENT.md`](./DEPLOYMENT.md))*

This guide provides step-by-step instructions for deploying the PostCare Multi-Hospital Post-Discharge Outreach Platform to production.

## Target Architecture

- **Frontend**: Vercel (React + Vite SPA)
- **Backend**: Render Python Web Service (FastAPI + AsyncSQLAlchemy + Uvicorn + Python 3.11.9)
- **Database**: Neon PostgreSQL / Render PostgreSQL (with SSL/TLS `prepare_database_config` normalization)
- **Redis Cache & Queue**: Upstash Redis (Serverless / Managed Redis)
- **AI Triage & Clinical Assessment**: Google Gemini API (`gemini-3.5-flash`)

---

## 1. Database Provisioning (Neon / Render PostgreSQL)

1. Provision PostgreSQL instance on Neon or Render.
2. Connection string format: `postgresql://user:password@ep-xyz.neon.tech/postcare?sslmode=require&channel_binding=require`.
3. **Automatic Normalization**: PostCare's database layer ([`backend/app/core/database.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/core/database.py)) automatically parses the connection string, strips asyncpg-incompatible libpq options (`sslmode`, `channel_binding`), and enforces `connect_args={'ssl': 'require'}` so TLS encryption remains active without driver exceptions.

---

## 2. Cache & Queue Provisioning (Upstash Redis)

1. Provision Redis database in Upstash Console.
2. Copy the **Redis URL** (e.g. `rediss://default:PASSWORD@xxxx.upstash.io:6379`).

---

## 3. Backend Deployment (Render Web Service)

1. In **Render Dashboard**, create **New Web Service**.
2. Service parameters:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3` (Pinned to `3.11.9` via `.python-version`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/v1/observability/health`

3. Configure Environment Variables in Render:
   | Variable | Value / Description |
   |---|---|
   | `ENV` | `production` |
   | `DATABASE_URL` | `<Neon or Render PostgreSQL Connection URL>` |
   | `REDIS_URL` | `<Upstash Redis URL>` |
   | `CORS_ORIGINS` | `https://your-vercel-app.vercel.app,http://localhost:5173` |
   | `PUBLIC_BASE_URL` | `https://your-render-backend.onrender.com` |
   | `AI_PROVIDER` | `gemini` |
   | `AI_MODEL` | `gemini-3.5-flash` |
   | `AI_FALLBACK_TO_MOCK` | `false` |
   | `GEMINI_API_KEY` | `<Your Google Gemini API Key>` |
   | `JWT_SECRET` | `<Secure random 32+ character string>` |
   | `CONSENSUS_POLICY` | `STRICT_CONSERVATIVE` |

---

## 4. Production Database Initialization & Demo Seeding

Once deployed on Render, execute non-destructive database initialization:

### Step 4.1: Initialize Schema (Non-Destructive)
```bash
python -m app.scripts.init_prod_db
```
*Creates missing database tables using `Base.metadata.create_all`. Never drops or alters existing data.*

### Step 4.2: Populate Initial Seed Data (Safe & Idempotent)
```bash
python -m app.scripts.seed_prod_demo
```
*Checks if Hospital records exist. If empty, populates initial demo data with `drop_existing=False`.*

---

## 5. Frontend Deployment (Vercel)

1. Import `PostCare` repository into Vercel.
2. Service parameters:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Environment Variables:
   - `VITE_API_BASE_URL`: `https://your-render-backend.onrender.com/api/v1`

---

## 6. Verification Checklist

1. **Backend Health Check**: `GET /api/v1/observability/health` -> HTTP 200 `"status": "HEALTHY"`.
2. **CORS Headers**: Verify API login returns `Access-Control-Allow-Origin` matching Vercel domain.
3. **Safety Evaluation**: `POST /api/v1/evaluation/run` -> HTTP 200 (`0% False Negative Rate`).
