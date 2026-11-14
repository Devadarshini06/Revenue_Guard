from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.analytics.engine import AnalyticsEngine

router = APIRouter(prefix="/products", tags=["Product Insights"])

@router.get("/performance")
def get_products_performance(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_top_products(start_date, end_date, category_id, limit=limit)

@router.get("/best-sellers")
def get_best_sellers(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(5),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    prods = engine.get_top_products(start_date, end_date, limit=limit)
    return prods

@router.get("/low-performers")
def get_low_performers(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(5),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    all_prods = engine.get_top_products(start_date, end_date, limit=100)
    # Sort ascending
    low = sorted(all_prods, key=lambda x: x["revenue"])[:limit]
    return low

