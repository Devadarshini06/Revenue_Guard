from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.analytics.engine import AnalyticsEngine

router = APIRouter(prefix="/regional", tags=["Regional Analysis"])

@router.get("/performance")
def get_regional_performance(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_regional_breakdown(start_date, end_date)

