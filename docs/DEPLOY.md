# Deploying AgentProbe to Railway + Vercel

> Step-by-step deploy guide. Path is **Railway (FastAPI + Postgres)** for the
> backend and **Vercel (Next.js)** for the frontend, wired together via env
> vars and CORS. Estimated time: 30–45 minutes if both account dashboards
> behave.

---

## Prerequisites

- A GitHub account with the `AgentProbe` repo pushed (this repo).
- A Railway account (railway.app) with a payment method on file. The free tier covers a small demo deploy.
- A Vercel account (vercel.com). Free tier is fine.
- Optional: a Groq API key (`https://console.groq.com`) so the deployed agent can actually run real inferences. The seeded demo runs work without any key.

---

## Step 1 — Backend on Railway

### 1.1 Create the project

1. Go to https://railway.app/new.
2. Choose **Deploy from GitHub repo** and pick `soneeee22000/AgentProbe`.
3. When prompted for the root directory, set it to **`backend`** (Railway will pick up `backend/Dockerfile` automatically because `railway.toml` declares the dockerfile builder).
4. Let the first build kick off so Railway provisions a service. It will fail on health-check — that's expected; we have no Postgres or env vars yet.

### 1.2 Add Postgres

1. In the project view, click **+ New** → **Database** → **PostgreSQL**.
2. Once provisioned, open the Postgres service → **Variables**, copy the `DATABASE_URL` value (looks like `postgresql://postgres:...@...railway.app:5432/railway`).

### 1.3 Configure backend env vars

Open the **backend** service → **Variables** tab → **Raw Editor**, paste:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
SEED_DEMO_ON_STARTUP=true
CORS_ORIGINS_EXTRA=https://YOUR-VERCEL-URL.vercel.app
ENVIRONMENT=production
JWT_SECRET=GENERATE-A-LONG-RANDOM-STRING-HERE
AUTH_ENABLED=false
RATE_LIMIT_RPM=60

# Optional — only if you want the deployed agent to actually run inference:
# GROQ_API_KEY=...
# OPENAI_API_KEY=...
# ANTHROPIC_API_KEY=...
# GOOGLE_API_KEY=...
# TAVILY_API_KEY=...
```

> The `${{Postgres.DATABASE_URL}}` syntax is Railway's variable reference — it
> resolves to the Postgres service's connection string at deploy time.

**Note on `DATABASE_URL`:** Railway hands out URLs like `postgresql://...` (sync dialect). The backend automatically rewrites these to `postgresql+asyncpg://...` at boot, so you can paste the value directly without modification.

### 1.4 Trigger a fresh deploy

After saving env vars, hit **Deploy → Redeploy**. Watch the logs:

- ✓ `alembic upgrade head` — migrations apply.
- ✓ `[maybe_seed] demo runs seeded.`
- ✓ `Uvicorn running on http://0.0.0.0:8000`.
- ✓ Health check at `/api/v1/health` returns 200.

Once green, copy the public URL Railway assigns (Settings → **Networking** → **Generate Domain**, e.g. `agentprobe-production.up.railway.app`).

### 1.5 Smoke test

```bash
curl https://YOUR-RAILWAY-URL/api/v1/runs/demo-fail-001 | jq
```

You should see the seeded failure trace.

---

## Step 2 — Frontend on Vercel

### 2.1 Import the project

1. Go to https://vercel.com/new.
2. Import the `AgentProbe` repo.
3. **Framework preset:** Next.js (auto-detected).
4. **Root directory:** `frontend`.
5. **Environment variable:**
   - `NEXT_PUBLIC_API_URL` = `https://YOUR-RAILWAY-URL` (no trailing slash).
6. Click **Deploy**.

### 2.2 Update CORS

Once Vercel assigns its URL (e.g. `agentprobe-xyz.vercel.app`), go back to Railway → backend service → Variables and set:

```
CORS_ORIGINS_EXTRA=https://agentprobe-xyz.vercel.app
```

Redeploy backend so the new origin is whitelisted.

### 2.3 Smoke test

Open `https://YOUR-VERCEL-URL/runs/demo-fail-001` in the browser. The Decision Graph should render with the red `WEATHER_FORECAST` failure node.

If you see CORS errors in the browser console, the `CORS_ORIGINS_EXTRA` value doesn't match the Vercel origin exactly (check trailing slashes, http vs https).

---

## Step 3 — GitHub Actions auto-deploy (optional)

If you want every push to master to redeploy:

1. **Railway → Project Settings → Tokens →** create a deploy token. Add to GitHub Secrets as `RAILWAY_TOKEN`.
2. **Vercel → Account Settings → Tokens →** create a token. Add as `VERCEL_TOKEN`.
3. Get `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` from `frontend/.vercel/project.json` after running `vercel link` locally, or from the Vercel project settings page.
4. Add all four to **GitHub repo → Settings → Secrets and variables → Actions**.

The existing `.github/workflows/deploy.yml` already wires these.

---

## Tear down (after the demo)

If the deploy is no longer needed:

1. Railway: Project → Settings → **Delete Project**.
2. Vercel: Project → Settings → **Delete Project**.

Both stop billing immediately.

---

## Demo URLs (fill in after deploy)

- Backend health: `https://________.up.railway.app/api/v1/health`
- Frontend home: `https://________.vercel.app/`
- Demo failure run: `https://________.vercel.app/runs/demo-fail-001`
- Demo happy run: `https://________.vercel.app/runs/demo-happy-001`
