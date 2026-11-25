from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from backend.database import get_db
from backend.analytics.engine import AnalyticsEngine
from backend.auth.dependencies import require_permission
from backend.auth.rbac import Permission

router = APIRouter(
    prefix="/refunds",
    tags=["Refund Analysis"],
    dependencies=[Depends(require_permission(Permission.VIEW_ANALYTICS))]
)

@router.get("/summary")
def get_refund_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    cur_start, cur_end, _, _ = engine.get_date_bounds(start_date, end_date)

    query = """
    SELECT 
        COUNT(DISTINCT r.id) AS total_refunds_count,
        COUNT(DISTINCT r.order_id) AS refunded_orders_count,
        COALESCE(SUM(r.refund_amount), 0.0) AS total_refund_amount,
        (SELECT COALESCE(SUM(oi.gross_revenue), 1.0) FROM order_items oi JOIN orders o ON oi.order_id = o.id WHERE o.order_date >= :start_date AND o.order_date <= :end_date) AS gross_revenue
    FROM refunds r
    WHERE r.refund_date >= :start_date AND r.refund_date <= :end_date;
    """
    row = db.execute(text(query), {"start_date": cur_start, "end_date": cur_end}).mappings().first()

    total_ref = float(row["total_refund_amount"] or 0)
    gross_rev = float(row["gross_revenue"] or 1.0)
    refund_rate = round((total_ref * 100.0 / gross_rev), 2)

    return {
        "total_refund_amount": round(total_ref, 2),
        "total_refunds_count": int(row["total_refunds_count"] or 0),
        "refunded_orders_count": int(row["refunded_orders_count"] or 0),
        "refund_rate": refund_rate
    }

@router.get("/reasons")
def get_refund_reasons(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_refund_reasons(start_date, end_date)

@router.get("/by-category")
def get_refunds_by_category(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    cur_start, cur_end, _, _ = engine.get_date_bounds(start_date, end_date)

    query = """
    SELECT 
        c.name AS category_name,
        COUNT(r.id) AS refund_count,
        ROUND(COALESCE(SUM(r.refund_amount), 0.0), 2) AS refund_amount,
        ROUND(COALESCE(SUM(oi.gross_revenue), 0.0), 2) AS category_revenue,
        CASE 
            WHEN SUM(oi.gross_revenue) > 0 
            THEN ROUND(SUM(r.refund_amount) * 100.0 / SUM(oi.gross_revenue), 2)
            ELSE 0.0 
        END AS refund_rate
    FROM categories c
    JOIN products p ON c.id = p.category_id
    JOIN order_items oi ON p.id = oi.product_id
    JOIN orders o ON oi.order_id = o.id
    LEFT JOIN refunds r ON oi.id = r.order_item_id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date
    GROUP BY c.name
    ORDER BY refund_amount DESC;
    """
    rows = db.execute(text(query), {"start_date": cur_start, "end_date": cur_end}).mappings().all()
    return [dict(r) for r in rows]

@router.get("/high-refund-products")
def get_high_refund_products(
    limit: int = Query(15),
    db: Session = Depends(get_db)
):
    query = """
    SELECT 
        p.id AS product_id,
        p.sku,
        p.name AS product_name,
        c.name AS category_name,
        COUNT(r.id) AS refund_claims,
        ROUND(COALESCE(SUM(r.refund_amount), 0.0), 2) AS total_refunded,
        ROUND(COALESCE(SUM(oi.gross_revenue), 0.0), 2) AS gross_sales,
        CASE 
            WHEN SUM(oi.gross_revenue) > 0 
            THEN ROUND(SUM(r.refund_amount) * 100.0 / SUM(oi.gross_revenue), 2)
            ELSE 0.0 
        END AS refund_rate
    FROM products p
    JOIN categories c ON p.category_id = c.id
    JOIN order_items oi ON p.id = oi.product_id
    LEFT JOIN refunds r ON oi.id = r.order_item_id
    GROUP BY p.id, p.sku, p.name, c.name
    HAVING COUNT(r.id) > 0
    ORDER BY total_refunded DESC
    LIMIT :limit;
    """
    rows = db.execute(text(query), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]

