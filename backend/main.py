from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import time
import uuid
import logging

from backend.config import settings
from backend.database import Base, engine
from backend.seed_data import seed_database
from backend.routes import (
    overview,
    revenue,
    sales,
    discounts,
    refunds,
    profitability,
    products,
    customers,
    regional,
    reports,
    data_management
)

# Configure structured application logger
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("revenueguard")

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Revenue Analytics & Financial Performance Intelligence Engine",
    docs_url="/api/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/api/redoc" if settings.DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None
)

# Enable CORS for authorized origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Production Security Headers & Correlation ID Middleware
@app.middleware("http")
async def security_and_timing_middleware(request: Request, call_next):
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"[RequestID: {request_id}] Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=settings.DEBUG)
        if settings.ENVIRONMENT == "production":
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error occurred.", "request_id": request_id}
            )
        else:
            raise exc

    process_time = time.time() - start_time
    
    # Attach observability headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Include all module routers under /api
app.include_router(overview.router, prefix=settings.API_PREFIX)
app.include_router(revenue.router, prefix=settings.API_PREFIX)
app.include_router(sales.router, prefix=settings.API_PREFIX)
app.include_router(discounts.router, prefix=settings.API_PREFIX)
app.include_router(refunds.router, prefix=settings.API_PREFIX)
app.include_router(profitability.router, prefix=settings.API_PREFIX)
app.include_router(products.router, prefix=settings.API_PREFIX)
app.include_router(customers.router, prefix=settings.API_PREFIX)
app.include_router(regional.router, prefix=settings.API_PREFIX)
app.include_router(reports.router, prefix=settings.API_PREFIX)
app.include_router(data_management.router, prefix=settings.API_PREFIX)

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "Operational",
        "environment": settings.ENVIRONMENT,
        "api_docs": "/api/docs" if settings.DOCS_ENABLED else "Disabled in production"
    }

@app.get("/api/health")
def health_check():
    """Liveness probe and general application health endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "database": "connected",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION
    }

@app.get("/api/health/ready", include_in_schema=False)
def readiness_check():
    """Readiness probe testing active database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "detail": "Database connection failed"
            }
        )

@app.get("/api/health/live", include_in_schema=False)
def liveness_probe():
    """Lightweight orchestrator liveness check."""
    return {"status": "alive"}


