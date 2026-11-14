from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

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

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Revenue Analytics & Financial Performance Intelligence Engine",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance Timing Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
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
        "api_docs": "/api/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "database": "connected"
    }

