# PostCare Production Deployment Guide

This guide provides step-by-step instructions for deploying the PostCare Multi-Hospital Post-Discharge Outreach Platform to production.

## Target Architecture

- **Frontend**: Vercel (React + Vite SPA)
- **Backend**: Render Python Web Service (FastAPI + AsyncSQLAlchemy + Uvicorn)
- **Database**: Render PostgreSQL
- **Redis Cache & Queue**: Upstash Redis (Serverless / Managed Redis)
- **AI Triage & Clinical Assessment**: Google Gemini API (`gemini-3.5-flash`)

---

## 1. Database Provisioning (Render PostgreSQL)

1. Log into your **Render Dashboard** and click **New +** -> **PostgreSQL**.
2. Set instance parameters:
   - **Name**: `postcare-db`
   - **Database**: `postcare`
   - **User**: `postcare_user`
   - **Region**: Select your preferred region (e.g. Oregon or Frankfurt).
3. Once created, copy the **Internal Database URL** (e.g., `postgres://postcare_user:PASSWORD@dpg-xxxx-a/postcare`).

> **Note**: PostCare's database layer (`backend/app/core/database.py`) automatically converts `postgres://` or `postgresql://` connection strings to use the `postgresql+asyncpg://` async driver.

---

## 2. Cache & Queue Provisioning (Upstash Redis)

1. Log into **Upstash Console** (https://console.upstash.com) and click **Create Database**.
2. Set settings:
   - **Name**: `postcare-redis`
   - **Type**: Regional / Standard
   - **Region**: Match your Render region for optimal latency.
3. Copy the **Redis URL** from the database dashboard (e.g., `rediss://default:PASSWORD@xxxx.upstash.io:6379`).

---

## 3. Backend Deployment (Render Web Service)

1. In the **Render Dashboard**, click **New +** -> **Web Service**.
2. Connect your Git repository (`PostCare`).
3. Configure service settings:
   - **Name**: `postcare-backend`
   - **Region**: Same as PostgreSQL
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/v1/observability/health`

4. Configure **Environment Variables** in Render Dashboard:
   | Variable | Value / Description |
   |---|---|
   | `ENV` | `production` |
   | `DATABASE_URL` | `<Render PostgreSQL Internal Database URL>` |
   | `REDIS_URL` | `<Upstash Redis URL>` |
   | `CORS_ORIGINS` | `https://<your-vercel-frontend-domain>.vercel.app,http://localhost:5173` |
   | `PUBLIC_BASE_URL` | `https://postcare-backend.onrender.com` |
   | `AI_PROVIDER` | `gemini` |
   | `AI_MODEL` | `gemini-3.5-flash` |
   | `AI_FALLBACK_TO_MOCK` | `false` |
   | `GEMINI_API_KEY` | `<Your Google Gemini API Key>` |
   | `JWT_SECRET` | `<Secure random 32+ character string>` |
   | `CONSENSUS_POLICY` | `STRICT_CONSERVATIVE` |

5. Deploy the Web Service.

---

## 4. Production Database Initialization & Demo Seeding

Once the backend service is deployed on Render, execute the non-destructive initialization steps using the Render Shell or one-time job CLI:

### Step 4.1: Initialize Schema (Non-Destructive)
Run the production table creation script:
```bash
python -m app.scripts.init_prod_db
```
*This creates all missing database tables without dropping or modifying existing data.*

### Step 4.2: Populate Initial Seed Data (Safe & Idempotent)
Populate default hospitals, system admin users, clinical protocols, and synthetic patients:
```bash
python -m app.scripts.seed_prod_demo
```
*This script is idempotent: it verifies whether Hospital records exist and skips seeding if data is already present.*

> [!CAUTION]
> **NEVER run `python -m app.scripts.reset_demo` or `python -m app.scripts.seed_data` in production.** Those scripts are for local development and contain destructive `drop_all` / table deletion logic.

---

## 5. Frontend Deployment (Vercel)

1. Log into **Vercel Dashboard** (https://vercel.com) and click **Add New...** -> **Project**.
2. Import the `PostCare` repository.
3. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

4. Configure **Environment Variables** in Vercel:
   | Variable | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://postcare-backend.onrender.com/api/v1` |

5. Click **Deploy**.

---

## 6. Post-Deployment Verification Checklist

1. **Backend Health Check**:
   Navigate to `https://postcare-backend.onrender.com/api/v1/observability/health`. Verify HTTP status 200 and `"status": "HEALTHY"`.

2. **CORS Verification**:
   Open the Vercel frontend app in your browser, open Developer Tools -> Network, and verify API login calls return `Access-Control-Allow-Origin: https://<your-vercel-frontend-domain>.vercel.app`.

3. **Live Call Simulation & Gemini Triage**:
   In the Campaign Manager tab, trigger an outreach call simulation. Verify Gemini 3.5 Flash processes the call and generates Assessment A & Assessment B in the Clinical Reviewer dashboard.
