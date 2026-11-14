from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from backend.database import get_db
from backend.analytics.engine import AnalyticsEngine

router = APIRouter(prefix="/profitability", tags=["Profitability Analysis"])

@router.get("/summary")
def get_profit_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    cur_start, cur_end, _, _ = engine.get_date_bounds(start_date, end_date)

    query = """
    SELECT 
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.discount_amount), 0.0) AS discounts,
        COALESCE(SUM(r.refund_amount), 0.0) AS refunds,
        (COALESCE(SUM(oi.net_revenue), 0.0) - COALESCE(SUM(r.refund_amount), 0.0)) AS net_revenue,
        COALESCE(SUM(oi.cogs), 0.0) AS cogs,
        (COALESCE(SUM(oi.net_revenue), 0.0) - COALESCE(SUM(r.refund_amount), 0.0) - COALESCE(SUM(oi.cogs), 0.0)) AS gross_profit
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN refunds r ON oi.id = r.order_item_id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date;
    """
    row = db.execute(text(query), {"start_date": cur_start, "end_date": cur_end}).mappings().first()

    net_rev = float(row["net_revenue"] or 0)
    profit = float(row["gross_profit"] or 0)
    margin = round((profit * 100.0 / net_rev), 2) if net_rev > 0 else 0.0

    return {
        "gross_revenue": round(float(row["gross_revenue"] or 0), 2),
        "discounts": round(float(row["discounts"] or 0), 2),
        "refunds": round(float(row["refunds"] or 0), 2),
        "net_revenue": round(net_rev, 2),
        "cost_of_goods_sold": round(float(row["cogs"] or 0), 2),
        "gross_profit": round(profit, 2),
        "profit_margin": margin
    }

@router.get("/monthly-trends")
def get_profit_trends(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    return engine.get_monthly_revenue_trend(start_date, end_date)

@router.get("/product-quadrant")
def get_profit_product_quadrant(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Classifies products into High Rev/High Margin, High Rev/Low Margin, Low Rev/High Margin, Low Rev/Low Margin."""
    engine = AnalyticsEngine(db)
    products = engine.get_top_products(start_date, end_date, limit=50)

    if not products:
        return []

    median_rev = sum(p["revenue"] for p in products) / len(products)
    median_margin = 35.0

    quadrant = []
    for p in products:
        is_high_rev = p["revenue"] >= median_rev
        is_high_margin = p["profit_margin"] >= median_margin

        if is_high_rev and is_high_margin:
            classification = "Star (High Revenue, High Margin)"
        elif is_high_rev and not is_high_margin:
            classification = "Workhorse (High Revenue, Low Margin)"
        elif not is_high_rev and is_high_margin:
            classification = "Niche Opportunity (Low Revenue, High Margin)"
        else:
            classification = "Underperformer (Low Revenue, Low Margin)"

        quadrant.append({
            **p,
            "classification": classification,
            "is_high_revenue": is_high_rev,
            "is_high_margin": is_high_margin
        })

    return quadrant

