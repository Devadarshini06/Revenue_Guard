from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from backend.database import get_db
from backend.analytics.engine import AnalyticsEngine

router = APIRouter(prefix="/customers", tags=["Customer Insights"])

@router.get("/summary")
def get_customer_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    cur_start, cur_end, _, _ = engine.get_date_bounds(start_date, end_date)

    query = """
    SELECT 
        COUNT(DISTINCT c.id) AS total_customers,
        COUNT(DISTINCT o.id) AS active_orders,
        COALESCE(SUM(oi.net_revenue), 0.0) AS total_revenue
    FROM customers c
    LEFT JOIN orders o ON c.id = o.customer_id AND o.order_date >= :start_date AND o.order_date <= :end_date
    LEFT JOIN order_items oi ON o.id = oi.order_id;
    """
    row = db.execute(text(query), {"start_date": cur_start, "end_date": cur_end}).mappings().first()

    total_cust = int(row["total_customers"] or 0)
    total_rev = float(row["total_revenue"] or 0)
    avg_spend = round((total_rev / total_cust), 2) if total_cust > 0 else 0.0

    return {
        "total_customers": total_cust,
        "active_orders": int(row["active_orders"] or 0),
        "total_revenue": round(total_rev, 2),
        "average_customer_spending": avg_spend
    }

@router.get("/segmentation")
def get_customer_segments(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_customer_segments(start_date, end_date)

@router.get("/top-customers")
def get_top_customers(
    limit: int = Query(15),
    db: Session = Depends(get_db)
):
    query = """
    SELECT 
        c.id,
        c.customer_code,
        c.name,
        c.segment,
        c.email,
        r.name AS region_name,
        COUNT(DISTINCT o.id) AS total_orders,
        ROUND(COALESCE(SUM(oi.net_revenue), 0.0), 2) AS total_spent,
        ROUND(COALESCE(SUM(rf.refund_amount), 0.0), 2) AS refund_total
    FROM customers c
    JOIN regions r ON c.region_id = r.id
    LEFT JOIN orders o ON c.id = o.customer_id
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN refunds rf ON oi.id = rf.order_item_id
    GROUP BY c.id, c.customer_code, c.name, c.segment, c.email, r.name
    ORDER BY total_spent DESC
    LIMIT :limit;
    """
    rows = db.execute(text(query), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]

