# RevenueGuard – Production Deployment & Operations Guide

**Milestone:** Phase 3, Milestone 7 – Production Readiness & Deployment Preparation  
**Target Environment:** Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9) / Container Orchestration  
**Application Stack:** React (Vite/Nginx) + FastAPI (Python 3.12/Uvicorn) + SQLite (WAL Mode) / PostgreSQL  

---

## 1. Overview & Architecture

RevenueGuard is designed for flexible enterprise deployment either as:
1. **Containerized Multi-Service Deployment (Recommended):** Docker & Docker Compose or Kubernetes with isolated frontend (Nginx) and backend (FastAPI) containers.
2. **Virtual Machine / Bare-Metal Deployment:** Systemd service units managed behind a host Nginx reverse proxy.

```
       [ Client HTTPS Request (Port 443) ]
                       │
                       ▼
         [ Nginx Reverse Proxy / TLS ]
         ┌─────────────┴─────────────┐
         ▼                           ▼
[ / -> Static React SPA ]   [ /api/* -> FastAPI Backend ]
  (Nginx Alpine / Dist)       (Uvicorn Workers / Port 8000)
                                     │
                                     ▼
                            [ Database Storage ]
                        (SQLite WAL or PostgreSQL 15+)
```

---

## 2. Prerequisites & System Requirements

### Hardware Sizing
- **Minimal (Up to 10,000 orders):** 2 vCPU, 4 GB RAM, 20 GB SSD storage.
- **Recommended (Enterprise 50,000+ orders):** 4 vCPU, 8 GB RAM, 50 GB High-IOPS NVMe storage.

### Software Requirements
- **Docker:** Engine v24.0+ and Compose v2.20+ OR
- **Python:** 3.12+ (with `venv` and `pip`)
- **Node.js:** 20+ LTS (with `npm`)
- **Nginx:** 1.22+
- **OpenSSL:** 3.0+

---

## 3. Containerized Deployment (Docker Compose)

### Step 1: Clone Repository & Setup Environment
```bash
git clone <repository-url> revenueguard
cd revenueguard

# Copy the production environment template
cp .env.example .env

# Edit .env with production parameters
nano .env
```

Ensure the following variables are configured in `.env`:
```ini
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=generate-a-secure-random-64-character-string-here
ALLOWED_ORIGINS=https://revenueguard.yourdomain.com
DOCS_ENABLED=False
DATABASE_URL=sqlite:///./data/revenueguard.db
```

### Step 2: Build and Launch Containers
```bash
# Build multi-stage images and start in background
docker compose up -d --build

# Verify container health
docker compose ps
```

### Step 3: Verify Container Health Probes
```bash
# Backend readiness check
curl -f http://127.0.0.1:8000/api/health/ready

# Frontend health check
curl -f http://127.0.0.1:80/
```

---

## 4. Bare-Metal / Virtual Machine Deployment (Systemd)

For environments operating without Docker, deploy using native Linux system services.

### Step 1: System User & Directories
```bash
# Create dedicated unprivileged system user
sudo useradd -r -s /bin/false -d /opt/revenueguard rguser

# Create application directories
sudo mkdir -p /opt/revenueguard /var/log/revenueguard /var/backups/revenueguard
sudo chown -R rguser:rguser /opt/revenueguard /var/log/revenueguard /var/backups/revenueguard
```

### Step 2: Backend Setup
```bash
cd /opt/revenueguard
sudo -u rguser python3.12 -m venv venv
sudo -u rguser ./venv/bin/pip install --upgrade pip
sudo -u rguser ./venv/bin/pip install -r requirements.txt
```

### Step 3: Frontend Build
```bash
cd /opt/revenueguard/frontend
npm ci
npm run build
# Artifacts generated in /opt/revenueguard/frontend/dist
```

### Step 4: Systemd Service Configuration
Create `/etc/systemd/system/revenueguard-backend.service`:
```ini
[Unit]
Description=RevenueGuard Enterprise Analytics Backend
After=network.target

[Service]
Type=simple
User=rguser
Group=rguser
WorkingDirectory=/opt/revenueguard
EnvironmentFile=/opt/revenueguard/.env
ExecStart=/opt/revenueguard/venv/bin/uvicorn backend.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 4 \
    --log-config /opt/revenueguard/backend/logging.conf
Restart=always
RestartSec=5
StandardOutput=append:/var/log/revenueguard/backend.log
StandardError=append:/var/log/revenueguard/backend_err.log

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable revenueguard-backend
sudo systemctl start revenueguard-backend
sudo systemctl status revenueguard-backend
```

### Step 5: Nginx Configuration
Copy the provided `nginx.conf` into `/etc/nginx/sites-available/revenueguard` and symlink to `sites-enabled`:
```bash
sudo ln -s /etc/nginx/sites-available/revenueguard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 5. PostgreSQL Migration Procedure

When transitioning from SQLite to a managed PostgreSQL cluster (e.g., AWS RDS, GCP Cloud SQL, or self-hosted PostgreSQL 15+):

1. **Provision PostgreSQL Database:**
   ```sql
   CREATE DATABASE revenueguard_prod;
   CREATE USER rguser WITH ENCRYPTED PASSWORD 'StrongSecretPassword123!';
   GRANT ALL PRIVILEGES ON DATABASE revenueguard_prod TO rguser;
   ```
2. **Update Application Connection String:**
   ```ini
   DATABASE_URL=postgresql://rguser:StrongSecretPassword123!@db-host.internal:5432/revenueguard_prod
   ```
3. **Execute Schema Migration & Data Load:**
   ```bash
   ./venv/bin/python -m backend.database --init
   # Or run database ingestion script for initial baseline records
   ./venv/bin/python -m backend.data_manager --seed
   ```
4. **Verify Schema & Record Counts:**
   ```sql
   SELECT count(*) FROM orders; -- Must match 5,200
   ```

---

## 6. Automated Backup & Recovery Procedures

### 6.1 Configuring Automated Backups
Schedule daily online SQLite backups via cron:

Create `/etc/cron.d/revenueguard-backup`:
```cron
# Run daily online SQLite backup at 02:00 AM UTC
0 2 * * * rguser /opt/revenueguard/venv/bin/python /opt/revenueguard/backend/database_backup.py backup --db /opt/revenueguard/revenueguard.db --out /var/backups/revenueguard >> /var/log/revenueguard/backup.log 2>&1
```

### 6.2 Emergency Restore Procedure
In the event of data corruption or catastrophic hardware failure:

1. **Stop Application Services:**
   ```bash
   sudo systemctl stop revenueguard-backend
   # Or: docker compose stop backend
   ```
2. **Execute Database Restore:**
   ```bash
   /opt/revenueguard/venv/bin/python /opt/revenueguard/backend/database_backup.py restore \
       --backup /var/backups/revenueguard/revenueguard_backup_20261124_020000.db \
       --target /opt/revenueguard/revenueguard.db
   ```
3. **Restart Application Services:**
   ```bash
   sudo systemctl start revenueguard-backend
   # Or: docker compose start backend
   ```
4. **Validate API Readiness:**
   ```bash
   curl -f http://127.0.0.1:8000/api/health/ready
   ```

---

## 7. Zero-Downtime Deployment & Rollback Runbook

### Rolling Update Procedure (Docker Compose)
1. **Pull or Build New Images:**
   ```bash
   docker compose build --pull
   ```
2. **Apply Upgrades:**
   ```bash
   docker compose up -d --no-deps backend
   # Verify backend readiness
   docker compose exec backend curl -f http://127.0.0.1:8000/api/health/ready
   docker compose up -d --no-deps frontend
   ```
3. **Prune Stale Images:**
   ```bash
   docker image prune -f
   ```

### Immediate Rollback Procedure
If post-deployment smoke tests detect regressions:
1. **Revert Image / Git Commit:**
   ```bash
   git checkout HEAD~1
   docker compose up -d --build
   ```
2. **Restore Previous Database State (if migrations occurred):**
   Execute SQLite backup restore as outlined in Section 6.2.
3. **Verify Regression Clearance:**
   Execute backend test suite:
   ```bash
   ./venv/bin/python -m unittest discover tests
   ```

---

## 8. Release Verification Checklist

### Pre-Release Verification Checklist
- [ ] All 118 unit, integration, and E2E automated tests pass.
- [ ] Frontend static bundle compiles cleanly with 0 TypeScript/ESLint errors.
- [ ] Database contains exact baseline records (5,200 orders, 24,079 total records).
- [ ] `.env` file does not contain development secrets or default passwords.
- [ ] `DEBUG` is set to `False` and `ENVIRONMENT` is set to `production`.
- [ ] `ALLOWED_ORIGINS` is configured with authorized production FQDNs.
- [ ] HTTP Security headers (`X-Frame-Options`, `nosniff`, `HSTS`) are verified via curl.
- [ ] Health endpoints (`/api/health`, `/api/health/ready`) return status `healthy`.
- [ ] Fresh online database backup generated and verified.

### Post-Release Smoke Verification Checklist
- [ ] `GET /api/health` returns HTTP 200 `{"status": "healthy"}`.
- [ ] `GET /api/health/ready` returns HTTP 200 `{"status": "ready", "database": "connected"}`.
- [ ] Overview KPI cards render Net Realized Revenue ($25,900,147.21).
- [ ] Filter interactions (date ranges, category switches) execute without console errors.
- [ ] CSV file export generates valid downloadable reports.
- [ ] Request IDs appear in server access logs and HTTP response headers.
