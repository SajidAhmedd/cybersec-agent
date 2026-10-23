# Deploying CyberSecAgent

A free-tier deployment for a public demo:

| Part | Service | Notes |
|---|---|---|
| Frontend (Next.js) | Vercel | Root directory `frontend-next` |
| Backend (FastAPI) | Render (Docker web service) | Free instances sleep when idle; the first request after a pause can take ~1 minute |
| PostgreSQL | Neon | Needs `POSTGRES_SSLMODE=require` |
| Neo4j | Neo4j AuraDB Free | URI looks like `neo4j+s://xxxxxxxx.databases.neo4j.io` |
| LLM | Groq | Free tier, rate-limited |

Never commit `.env`. All secrets go into each platform's environment-variable settings.

## 1. Create the databases

**Neo4j AuraDB Free** - https://console.neo4j.io
1. Create a free instance.
2. Save the connection URI, username and password (the password is shown only once).

**Neon** - https://console.neon.tech
1. Create a project (pick the region closest to your Render region).
2. From the connection details, note the host, database name, user and password.

## 2. Seed the hosted databases

From the project root, point the app's settings at the hosted databases for this shell
(environment variables override `.env`) and run the seed script:

```powershell
$env:POSTGRES_HOST = "<neon host>"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB = "<neon database>"
$env:POSTGRES_USER = "<neon user>"
$env:POSTGRES_PASSWORD = "<neon password>"
$env:POSTGRES_SSLMODE = "require"
$env:NEO4J_URI = "<aura uri>"
$env:NEO4J_USER = "<aura username>"
$env:NEO4J_PASSWORD = "<aura password>"
venv\Scripts\python.exe scripts\seed_databases.py
```

Expected output: `PostgreSQL seeded - experts: 3` and the Neo4j node counts.
Close that terminal afterwards so the local app keeps using the Docker databases.

## 3. Deploy the backend on Render

https://dashboard.render.com → **New → Web Service** → connect the GitHub repo.

- **Runtime:** Docker (uses the `Dockerfile` in the repo root)
- **Instance type:** Free
- **Health check path:** `/health`
- **Environment variables:**

| Variable | Value |
|---|---|
| `LLM_PROVIDER` | `groq` |
| `GROQ_API_KEY` | your Groq key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` |
| `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Neon values |
| `POSTGRES_SSLMODE` | `require` |
| `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` | AuraDB values |
| `ALLOWED_ORIGINS` | your Vercel URL (set after step 4), e.g. `https://cybersec-agent.vercel.app` |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `OUTREACH_ENABLED` | `false` |

Leave `ADMIN_API_KEY` unset unless you need the expert write endpoints; when unset they are disabled.

When it is live, open `https://<your-service>.onrender.com/health/ready` - it should report
`"status": "ready"` with `postgres`, `neo4j` and `llm` all `true`.

## 4. Deploy the frontend on Vercel

https://vercel.com/new → import the GitHub repo.

- **Root directory:** `frontend-next`
- **Framework preset:** Next.js (detected automatically)
- **Environment variable:** `NEXT_PUBLIC_API_URL` = `https://<your-service>.onrender.com`

Deploy, then copy the production URL (e.g. `https://cybersec-agent.vercel.app`).

## 5. Connect the two

Back in Render, set `ALLOWED_ORIGINS` to the Vercel production URL and save (Render redeploys).
Without this the browser blocks the frontend's API calls (CORS).

## 6. Try it

Open the Vercel URL and describe an incident, e.g. "Our company website was hit by ransomware".
After a couple of answers the assistant presents matching experts; selecting one completes the handoff.

## Listing external freelancers

Besides the example experts, you can list real freelancers by their **public profile link**
(e.g. Upwork, Fiverr, Toptal, LinkedIn). They are shown with an "External freelancer profile -
not affiliated" notice and a "View profile" link; when chosen, the assistant tells the user to
contact them directly on that platform. Nobody is notified and no contact details are stored.

1. Copy the format from `scripts/external_experts.example.json` into `scripts/external_experts.json`.
2. Per freelancer, add only what their public profile shows: name, headline, platform, profile URL,
   and the matching `skills` / `platforms` / `services` (names must match the graph - the seed
   script lists the valid ones and ignores anything else). Don't copy photos, full bios, ratings
   or contact details.
3. Run `scripts/seed_databases.py` (locally, and with the hosted-database settings from step 2).
   Freelancers removed from the file are deactivated in both databases.

## Limits of the demo

- Chat sessions live in the backend's memory and are lost when the free instance sleeps or redeploys
  (conversations are still recorded in PostgreSQL).
- Each visitor IP gets `CHAT_RATE_LIMIT_PER_MINUTE` (10) and `CHAT_RATE_LIMIT_PER_DAY` (100) chat requests.
- The experts are demo data; notifications to experts are disabled (`OUTREACH_ENABLED=false`).
