# ChemVigil — Intelligent Literature Discovery Platform

Automated RSS ingestion, semantic matching, and personalized email push for scientific literature.

## Quick Start

### Prerequisites
- Python 3.10+
- (Optional) PostgreSQL 15+

### Setup

```bash
# 1. Clone & install
pip install -r backend/requirements.txt

# 2. Configure
cp backend/.env.example backend/.env
# Edit backend/.env — at minimum set SECRET_KEY and SMTP settings

# 3. Initialize journals
cd backend && python init_journals.py

# 4. Start server
cd .. && python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

# 5. Open in browser
# http://localhost:8000/app
```

### Windows Quick Start

```powershell
.\start.ps1
```

### Linux/Mac Quick Start

```bash
chmod +x start.sh && ./start.sh
```

## Configuration

All settings in `backend/.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | JWT signing key (generate a random string) |
| `DATABASE_URL` | No | Default: SQLite (`sqlite:///chemvigil.db`). Use PostgreSQL: `postgresql://user:pass@host:5432/chemvigil` |
| `SMTP_HOST` | No | SMTP server (e.g. `smtp.qq.com`) |
| `SMTP_PORT` | No | SMTP port (465 for SSL, 587 for TLS) |
| `SMTP_USER` | No | SMTP username (usually your email) |
| `SMTP_PASS` | No | SMTP password or app-specific password |
| `SMTP_FROM` | No | From address |
| `SENDGRID_API_KEY` | No | SendGrid API key (auto-fallback to SMTP) |
| `RESEND_API_KEY` | No | Resend API key (last fallback) |
| `BAIDU_APP_ID` | No | Baidu Translate App ID (for Chinese→English) |
| `BAIDU_API_KEY` | No | Baidu Translate API Key |
| `BAIDU_SECRET_KEY` | No | Baidu Translate Secret Key |
| `CORS_ORIGINS` | No | Comma-separated allowed origins (default: `*`) |
| `PUBLIC_URL` | No | Public-facing URL for verification links (default: `http://localhost:8000`) |

### Email Providers (auto-selected in order)

1. **SendGrid** — `SENDGRID_API_KEY` set
2. **SMTP** — `SMTP_HOST` set (supports SSL/TLS)
3. **Resend** — `RESEND_API_KEY` set

### PostgreSQL Setup

```bash
# Set DATABASE_URL in .env, then run:
python -c "from database.database import init_db; init_db()"
```

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Job Worker                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ FETCH_JOURNAL │  │ NEW_ARTICLES │  │  Other   │  │
│  │ (collect RSS) │  │ (match &     │  │  Jobs    │  │
│  │   → persist  │  │  push email) │  │          │  │
│  │   → embed    │  │              │  │          │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────────────────────────────────────────┐
│                   Database (SQLite/PostgreSQL)        │
│  Papers │ Journals │ Users │ Interests │ Matches    │
│  EmailDeliveries │ WeeklyReports │ Topics           │
└─────────────────────────────────────────────────────┘
         ▲
         │
┌─────────────────────────────────────────────────────┐
│              FastAPI Server (port 8000)              │
│  /api/auth/*  /api/search  /api/user/*  /api/jobs  │
│  /app (frontend SPA)                                │
└─────────────────────────────────────────────────────┘
```

## API Endpoints

### Auth
- `POST /api/auth/register` — Register new user
- `POST /api/auth/login` — Login
- `GET /api/auth/verify-email?token=xxx` — Verify email
- `POST /api/auth/resend-verify` — Resend verification email
- `GET /api/auth/me` — Get current user

### Jobs
- `POST /api/trigger-fetch` — Trigger RSS fetch
- `POST /api/trigger-push` — Match & push new articles
- `POST /api/trigger-summary` — Generate weekly report
- `POST /api/trigger-enrich` — Batch enrich abstracts
- `POST /api/trigger-resolve` — Resolve missing DOIs

### Email Deliveries
- `GET /api/email-deliveries` — List all deliveries
- `GET /api/email-deliveries/stats` — Delivery stats
- `POST /api/email-deliveries/retry` — Retry failed deliveries

## Frontend Pages

- **Literature Search** — Full-text search across all papers
- **Favorites** — Starred papers
- **Subscription** — Follow/unfollow RSS journals
- **Topics** — Define research interests (semantically matched)
- **Email Push** — Trigger fetch, matching, report generation
- **Settings** — Email config, verification status

## Maintenance

```bash
# Enrich missing abstracts
curl -X POST http://localhost:8000/api/trigger-enrich

# Retry failed email deliveries
curl -X POST http://localhost:8000/api/email-deliveries/retry

# Resolve missing DOIs
curl -X POST http://localhost:8000/api/trigger-resolve
```
