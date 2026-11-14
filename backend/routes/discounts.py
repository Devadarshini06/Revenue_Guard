from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from backend.database import get_db
from backend.analytics.engine import AnalyticsEngine

router = APIRouter(prefix="/discounts", tags=["Discount Analysis"])

@router.get("/summary")
def get_discount_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    cur_start, cur_end, _, _ = engine.get_date_bounds(start_date, end_date)

    query = """
    SELECT 
        COUNT(DISTINCT d.id) AS total_discount_instances,
        COALESCE(SUM(d.discount_amount), 0.0) AS total_discounts_given,
        COALESCE(AVG(d.discount_percentage), 0.0) AS average_discount_percentage,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS total_gross_value
    FROM discounts d
    JOIN orders o ON d.order_id = o.id
    JOIN order_items oi ON d.order_item_id = oi.id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date;
    """
    row = db.execute(text(query), {"start_date": cur_start, "end_date": cur_end}).mappings().first()

    total_gross = float(row["total_gross_value"] or 0)
    total_disc = float(row["total_discounts_given"] or 0)
    erosion_rate = round((total_disc * 100.0 / total_gross), 2) if total_gross > 0 else 0.0

    return {
        "total_discounts": round(total_disc, 2),
        "total_instances": int(row["total_discount_instances"] or 0),
        "average_discount_percentage": round(float(row["average_discount_percentage"] or 0), 2),
        "revenue_erosion_rate": erosion_rate
    }

@router.get("/by-type")
def get_discounts_by_type(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_discount_analysis(start_date, end_date)

@router.get("/by-category")
def get_discounts_by_category(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    cur_start, cur_end, _, _ = engine.get_date_bounds(start_date, end_date)

    query = """
    SELECT 
        c.name AS category_name,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(d.discount_amount), 0.0) AS discount_amount,
        CASE 
            WHEN SUM(oi.gross_revenue) > 0 
            THEN ROUND(SUM(d.discount_amount) * 100.0 / SUM(oi.gross_revenue), 2)
            ELSE 0.0 
        END AS discount_percentage
    FROM categories c
    JOIN products p ON c.id = p.category_id
    JOIN order_items oi ON p.id = oi.product_id
    JOIN orders o ON oi.order_id = o.id
    LEFT JOIN discounts d ON oi.id = d.order_item_id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date
    GROUP BY c.name
    ORDER BY discount_amount DESC;
    """
    rows = db.execute(text(query), {"start_date": cur_start, "end_date": cur_end}).mappings().all()
    return [dict(r) for r in rows]

@router.get("/high-discount-orders")
def get_high_discount_orders(
    min_pct: float = Query(15.0),
    limit: int = Query(25),
    db: Session = Depends(get_db)
):
    query = """
    SELECT 
        o.order_number,
        o.order_date,
        c.name AS customer_name,
        p.name AS product_name,
        oi.gross_revenue,
        d.discount_percentage,
        d.discount_amount,
        oi.net_revenue,
        oi.profit,
        d.reason
    FROM discounts d
    JOIN orders o ON d.order_id = o.id
    JOIN customers c ON o.customer_id = c.id
    JOIN order_items oi ON d.order_item_id = oi.id
    JOIN products p ON oi.product_id = p.id
    WHERE d.discount_percentage >= :min_pct
    ORDER BY d.discount_amount DESC
    LIMIT :limit;
    """
    rows = db.execute(text(query), {"min_pct": min_pct, "limit": limit}).mappings().all()
    return [dict(r) for r in rows]

