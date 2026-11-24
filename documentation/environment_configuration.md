# RevenueGuard – Production Environment Configuration Guide
## Environment Variables, Security Parameters, and Configuration Reference

**Document Version:** 1.0  
**Scope:** Backend (`.env`), Frontend (`frontend/.env`), and Orchestration Runtime  

---

## 1. Overview & Golden Rules

1. **Zero Committed Secrets**: Never commit actual `.env` files, API tokens, database connection strings, or cryptographic keys to version control.
2. **Fail-Fast Startup**: The application inspects critical settings on startup and logs an error if invalid parameters are detected.
3. **Environment Separation**: Distinct configuration profiles for `development`, `testing`, and `production`.

---

## 2. Backend Environment Variables Reference

| Variable Name | Required? | Default (Development) | Production Recommendation | Description |
|:---|:---:|:---:|:---:|:---|
| `ENVIRONMENT` | **Yes** | `development` | `production` | Sets execution environment profile (`development`, `testing`, `production`). |
| `DEBUG` | **Yes** | `true` | `false` | Enables debug logging and detailed exception traces. **Forced to false when `ENVIRONMENT=production`.** |
| `DOCS_ENABLED` | No | `true` | `false` | Enables interactive OpenAPI docs at `/api/docs` and `/api/redoc`. Recommended disabled in public production. |
| `DATABASE_URL` | **Yes** | `sqlite:///./revenueguard.db` | `sqlite:////app/data/revenueguard.db` or `postgresql://user:pass@host:5432/dbname` | Database connection string with driver prefix. |
| `SECRET_KEY` | **Yes** | `revenueguard-insecure-...` | *Cryptographically random 32+ char token* | Key used for cryptographic signing and session validation. |
| `ALLOWED_ORIGINS`| **Yes** | `*` (dev list) | `https://analytics.yourcompany.com` | Comma-separated list of origins permitted to make cross-origin requests. |
| `HOST` | No | `0.0.0.0` | `0.0.0.0` | Network interface IP to bind ASGI server to. |
| `PORT` | No | `8000` | `8000` | Port for ASGI HTTP server. |
| `WORKERS` | No | `1` | `4` | Number of concurrent Uvicorn worker processes. |

---

## 3. Frontend Environment Variables Reference

| Variable Name | Required? | Default | Production Value | Description |
|:---|:---:|:---:|:---:|:---|
| `VITE_API_URL` | **Yes** | `/api` | `/api` | Base API prefix for HTTP requests. In production, relative routing `/api` forwards through reverse proxy to backend. |

---

## 4. Environment Templates

### Root Backend Template (`.env.example`):
```bash
# ==============================================================================
# RevenueGuard Production Environment Variables
# ==============================================================================
ENVIRONMENT=production
DEBUG=false
DOCS_ENABLED=false

# Database Configuration
DATABASE_URL=sqlite:///./revenueguard.db
# DATABASE_URL=postgresql://rg_admin:strong_password@pg-host:5432/revenueguard_prod

# Cryptographic Secret Key (Generate with: openssl rand -hex 32)
SECRET_KEY=change-this-to-a-cryptographically-random-32-character-secret-key

# Allowed CORS Domains (comma-separated, no trailing slashes)
ALLOWED_ORIGINS=https://revenueguard.yourcompany.com

# Server Bind Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

### Frontend Template (`frontend/.env.example`):
```bash
# RevenueGuard Frontend Environment Configuration
VITE_API_URL=/api
```

---

## 5. Setup Instructions by Environment

### A. Local Development Setup
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set `ENVIRONMENT=development` and `DEBUG=true`.
3. In `frontend/`, copy `.env.example` to `.env`:
   ```bash
   cd frontend && cp .env.example .env
   ```
4. Start backend: `./venv/bin/uvicorn backend.main:app --reload --port 8000`
5. Start frontend: `npm --prefix frontend run dev`

### B. Production Container Deployment
1. Generate a production secret key:
   ```bash
   openssl rand -hex 32
   ```
2. Populate production environment file or inject via orchestrator secret manager (e.g. Kubernetes Secrets, AWS Secrets Manager).
3. Ensure `ENVIRONMENT=production`, `DEBUG=false`, and `DOCS_ENABLED=false`.
4. Restrict `ALLOWED_ORIGINS` to the exact enterprise domain name.

