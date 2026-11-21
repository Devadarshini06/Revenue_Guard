from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.analytics.engine import AnalyticsEngine

router = APIRouter(prefix="/revenue", tags=["Revenue Analytics"])

@router.get("/summary")
def get_revenue_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    kpis = engine.calculate_dashboard_kpis(start_date, end_date, region_id, category_id)
    return {
        "gross_revenue": kpis["total_revenue"],
        "net_revenue": kpis["net_revenue"],
        "discounts": kpis["total_discounts"],
        "refunds": kpis["total_refunds"],
        "growth_rate": kpis["net_revenue"]["change_percentage"]
    }

@router.get("/trends")
def get_revenue_trends(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region_id: Optional[int] = Query(None),
    grain: str = Query("monthly"),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_monthly_revenue_trend(start_date, end_date, region_id, grain=grain)

@router.get("/by-category")
def get_revenue_by_category(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_category_breakdown(start_date, end_date)

@router.get("/by-region")
def get_revenue_by_region(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_regional_breakdown(start_date, end_date)

@router.get("/by-product")
def get_revenue_by_product(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_top_products(start_date, end_date, category_id, limit=limit)

