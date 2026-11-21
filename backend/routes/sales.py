from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from backend.database import get_db
from backend.analytics.engine import AnalyticsEngine

router = APIRouter(prefix="/sales", tags=["Sales Performance"])

@router.get("/summary")
def get_sales_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    cur_start, cur_end, _, _ = engine.get_date_bounds(start_date, end_date)

    query = """
    SELECT 
        COUNT(DISTINCT o.id) AS total_orders,
        COALESCE(SUM(oi.quantity), 0) AS total_units_sold,
        COALESCE(SUM(oi.net_revenue), 0.0) AS total_sales,
        CASE 
            WHEN COUNT(DISTINCT o.id) > 0 
            THEN ROUND(SUM(oi.net_revenue) / COUNT(DISTINCT o.id), 2)
            ELSE 0.0 
        END AS average_order_value
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date
      AND (:region_id IS NULL OR o.region_id = :region_id);
    """
    row = db.execute(text(query), {"start_date": cur_start, "end_date": cur_end, "region_id": region_id}).mappings().first()

    return {
        "total_orders": int(row["total_orders"] or 0),
        "total_units_sold": int(row["total_units_sold"] or 0),
        "total_sales": round(float(row["total_sales"] or 0), 2),
        "average_order_value": round(float(row["average_order_value"] or 0), 2)
    }

@router.get("/payment-methods")
def get_sales_by_payment(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    cur_start, cur_end, _, _ = engine.get_date_bounds(start_date, end_date)

    query = """
    SELECT 
        o.payment_method,
        COUNT(DISTINCT o.id) AS orders_count,
        ROUND(SUM(oi.net_revenue), 2) AS total_amount,
        ROUND(AVG(oi.net_revenue), 2) AS avg_amount
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date
    GROUP BY o.payment_method
    ORDER BY total_amount DESC;
    """
    rows = db.execute(text(query), {"start_date": cur_start, "end_date": cur_end}).mappings().all()
    total_sales = sum(float(r["total_amount"] or 0) for r in rows)

    return [
        {
            "payment_method": r["payment_method"],
            "name": r["payment_method"],
            "orders_count": int(r["orders_count"] or 0),
            "count": int(r["orders_count"] or 0),
            "total_amount": round(float(r["total_amount"] or 0), 2),
            "revenue": round(float(r["total_amount"] or 0), 2),
            "value": round(float(r["total_amount"] or 0), 2),
            "avg_amount": round(float(r["avg_amount"] or 0), 2),
            "percentage": round(float(r["total_amount"] or 0) * 100.0 / total_sales, 2) if total_sales > 0 else 0.0
        }
        for r in rows
    ]

@router.get("/transactions")
def get_sales_transactions(
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_recent_transactions(search=search, limit=limit, offset=offset)

