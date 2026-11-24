# RevenueGuard – Production Deployment Architecture
## Enterprise Infrastructure, Scaling, and Service Topology Specification

**Document Version:** 1.0  
**Target Environment:** Containerized Microservice Topology / Cloud / On-Premises Kubernetes  
**Platform Components:** Nginx Edge Proxy -> FastAPI ASGI Application -> SQLite / PostgreSQL Database  

---

## 1. System Topology Overview

```
+---------------------------------------------------------------------------------------------------+
|                                      EXTERNAL INGRESS / INTERNET                                  |
|                                         (HTTPS / Port 443)                                        |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                       EDGE REVERSE PROXY                                          |
|                                       (Nginx / Caddy / ALB)                                       |
|                                                                                                   |
|   - SSL / TLS Termination (TLS 1.3, Let's Encrypt / Enterprise Cert)                              |
|   - HTTP Security Headers (HSTS, CSP, Frame-Options, Content-Type-Options)                        |
|   - Gzip / Brotli Compression for JS/CSS/SVG static chunks                                        |
|   - Rate Limiting (e.g. 100 req/min per IP, 10 req/min for file upload/validate)                  |
|   - Ingress Routing:                                                                              |
|       * Path '/'         -> Static Asset Cache (/usr/share/nginx/html)                            |
|       * Path '/api/'     -> Upstream ASGI Pool (http://backend:8000/api/)                         |
+------------------------+-------------------------------------------------+------------------------+
                         |                                                 |
                         v                                                 v
+---------------------------------------------------+     +-----------------------------------------+
|                  FRONTEND SERVICE                 |     |             BACKEND SERVICE             |
|              (Compiled React 18 / Vite)           |     |         (FastAPI / Uvicorn Cluster)     |
|                                                   |     |                                         |
|  - HTML5 History API Routing fallback             |     |  - ASGI Server: Uvicorn (4 Workers)     |
|  - In-Memory State & React Context               |     |  - Request Tracing (X-Request-ID)       |
|  - Recharts Visualizations                        |     |  - Latency Logging (X-Process-Time)     |
|  - Client-side File Validation (10 MB gate)       |     |  - Read-Only Lexical Guard & Authorizer |
|  - Binary Stream Downloader (CSV/Excel)           |     |  - 45 Normalized REST Endpoints         |
+---------------------------------------------------+     +--------------------+--------------------+
                                                                               |
                                                                               v
                                                          +-----------------------------------------+
                                                          |             DATABASE LAYER              |
                                                          |                                         |
                                                          |  Option A: SQLite 3 (Single Instance)   |
                                                          |    - Journal Mode: WAL                  |
                                                          |    - Busy Timeout: 30s                  |
                                                          |    - Persistent Docker Volume (rg-data) |
                                                          |                                         |
                                                          |  Option B: PostgreSQL 15+ (Clustered)   |
                                                          |    - Connection Pool: 20 + 10 Overflow  |
                                                          |    - Primary / Standby Replication      |
                                                          +-----------------------------------------+
```

---

## 2. Component Architecture & Sizing

### A. Frontend Layer (Static Asset Distribution)
- **Engine**: Nginx Alpine Linux container or CDN (Cloudflare, AWS CloudFront).
- **Resource Footprint**: Minimal (~10 MB RAM per replica, < 0.1 CPU cores).
- **Routing**: Configured with `try_files $uri $uri/ /index.html;` to allow direct page reloads on React client-side paths (`/revenue`, `/sales`, `/profitability`, `/settings`).
- **Caching Policy**: Static chunk bundles in `/assets/` have content hashes and are cached with `Cache-Control: public, max-age=31536000, immutable`. The `index.html` entry point is served with `Cache-Control: no-cache`.

### B. Backend Layer (FastAPI ASGI Server)
- **Engine**: Python 3.12 running Uvicorn ASGI workers.
- **Worker Configuration**: Recommended formula: `(2 * CPU cores) + 1` workers. For a standard 2-core container, 4 workers are configured:
  ```bash
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
  ```
- **Resource Footprint**: ~180 MB RAM baseline + 50 MB per active worker.
- **Connection Management**: Handles database connections via scoped SQLAlchemy sessions (`yield db` with guaranteed `db.close()` in finally block).

---

## 3. Database Scaling & Architectural Trade-offs

### SQLite Deployment Model (Single-Instance):
- **When to Use**: Small to mid-size internal enterprise deployments, isolated tenant installations, edge deployments, and single-host Docker Compose environments.
- **Storage Strategy**: Database file must reside on a persistent local storage volume (`/app/data/revenueguard.db`).
- **Concurrency Characteristics**: WAL mode allows unlimited concurrent readers alongside active writers. Write operations acquire a brief transactional lock (guarded by a 30-second busy timeout).
- **Limitations**: **Cannot scale horizontally across multiple container replicas.** If multiple container instances attempt to write to a single SQLite file over a network filesystem (NFS/CIFS), database corruption can occur due to unreliable POSIX advisory locking.

### PostgreSQL Deployment Model (High-Availability Clustered):
- **When to Use**: High-traffic enterprise environments, multi-region deployments, or horizontal container auto-scaling (Kubernetes HPA).
- **Configuration**: Set `DATABASE_URL=postgresql://user:password@pg-bouncer:5432/revenueguard_prod`.
- **Connection Pooling**: SQLAlchemy pool pre-configured in `backend/database.py` with `pool_size=20`, `max_overflow=10`, `pool_recycle=1800`, and `pool_pre_ping=True`.
- **Migration Path**: Analytical queries in `backend/analytics/sql_queries.py` are written in ANSI SQL, allowing drop-in compatibility.

---

## 4. Disaster Recovery & Availability SLA

| Metric | Target SLA | Implementation Strategy |
|:---|:---:|:---|
| **Recovery Point Objective (RPO)** | **< 1 Hour** | Hourly online snapshot backups via `backend/database_backup.py` shipped to encrypted off-site object storage (S3/GCS/Blob). |
| **Recovery Time Objective (RTO)** | **< 15 Minutes** | Automated restoration script `python -m backend.database_backup --restore <backup_file>`. Container recreation via Docker Compose. |
| **Service Uptime Target** | **99.9%** | Kubernetes liveness probe on `/api/health/live` and readiness probe on `/api/health/ready`. |

---

## 5. Security & Isolation Controls

1. **Non-Root Execution**: Backend container runs strictly as unprivileged user `rguser` (UID 1001, GID 1001).
2. **Network Segmentation**: In production, backend and database reside on private internal subnets without public ingress. Only the Nginx edge proxy is exposed to external traffic.
3. **Storage Isolation**: Persistent data is mounted into `/app/data/` with restricted POSIX permissions (`chmod 700`).
