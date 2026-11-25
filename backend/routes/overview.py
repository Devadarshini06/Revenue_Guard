from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from backend.database import get_db
from backend.analytics.engine import AnalyticsEngine
from backend.analytics.insights import InsightGenerator
from backend.models import Category, Region, Order
from backend.auth.dependencies import require_permission
from backend.auth.rbac import Permission

router = APIRouter(
    prefix="/overview",
    tags=["Overview"],
    dependencies=[Depends(require_permission(Permission.VIEW_ANALYTICS))]
)

@router.get("/filters")
def get_filter_options(db: Session = Depends(get_db)):
    categories = db.query(Category.id, Category.name, Category.code).all()
    regions = db.query(Region.id, Region.name, Region.code, Region.country).all()
    
    date_bounds = db.query(
        Order.order_date
    ).order_by(Order.order_date.asc()).first()
    
    latest_order = db.query(
        Order.order_date
    ).order_by(Order.order_date.desc()).first()

    min_date = date_bounds[0].strftime("%Y-%m-%d") if date_bounds and date_bounds[0] else "2024-01-01"
    max_date = latest_order[0].strftime("%Y-%m-%d") if latest_order and latest_order[0] else "2026-11-14"

    return {
        "categories": [{"id": c.id, "name": c.name, "code": c.code} for c in categories],
        "regions": [{"id": r.id, "name": r.name, "code": r.code, "country": r.country} for r in regions],
        "segments": ["Enterprise", "Mid-Market", "SMB", "Direct Consumer"],
        "payment_methods": ["Wire Transfer", "Credit Card", "ACH", "PayPal"],
        "min_date": min_date,
        "max_date": max_date
    }

@router.get("/kpis")
def get_kpis(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.calculate_dashboard_kpis(start_date, end_date, region_id, category_id)

@router.get("/trends")
def get_revenue_trends(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_monthly_revenue_trend(start_date, end_date, region_id)

@router.get("/category-breakdown")
def get_categories(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_category_breakdown(start_date, end_date)

@router.get("/top-products")
def get_top_products(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_top_products(start_date, end_date, category_id, limit=limit)

@router.get("/regional-sales")
def get_regional_sales(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_regional_breakdown(start_date, end_date)

@router.get("/recent-transactions")
def get_recent_transactions(
    search: Optional[str] = Query(None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_recent_transactions(search=search, limit=limit, offset=offset)

@router.get("/insights")
def get_business_insights(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    generator = InsightGenerator(db)
    return generator.generate_insights(start_date, end_date, region_id, category_id)

