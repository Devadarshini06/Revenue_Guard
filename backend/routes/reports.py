from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import io
import pandas as pd
from backend.database import get_db
from backend.analytics.engine import AnalyticsEngine
from backend.auth.dependencies import require_permission
from backend.auth.rbac import Permission

router = APIRouter(prefix="/reports", tags=["Reports & Exports"])

@router.get("/summary", dependencies=[Depends(require_permission(Permission.VIEW_ANALYTICS))])
def get_executive_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    kpis = engine.calculate_dashboard_kpis(start_date, end_date)
    categories = engine.get_category_breakdown(start_date, end_date)
    regions = engine.get_regional_breakdown(start_date, end_date)
    trends = engine.get_monthly_revenue_trend(start_date, end_date)

    return {
        "kpis": kpis,
        "categories": categories,
        "regions": regions,
        "trends": trends,
        "generated_at": pd.Timestamp.now().isoformat()
    }

@router.get("/export/transactions/csv", dependencies=[Depends(require_permission(Permission.EXPORT_REPORTS))])
def export_transactions_csv(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    transactions = engine.get_recent_transactions(search=search, limit=5000, offset=0)
    df = pd.DataFrame(transactions)
    
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = Response(content=stream.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=revenueguard_transactions.csv"
    return response

@router.get("/export/transactions/excel", dependencies=[Depends(require_permission(Permission.EXPORT_REPORTS))])
def export_transactions_excel(
    db: Session = Depends(get_db)
):
    engine = AnalyticsEngine(db)
    transactions = engine.get_recent_transactions(limit=5000, offset=0)
    df = pd.DataFrame(transactions)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Transactions", index=False)
        
        # Add monthly trend sheet
        trends_df = pd.DataFrame(engine.get_monthly_revenue_trend())
        trends_df.to_excel(writer, sheet_name="Monthly_Trends", index=False)

        # Add categories sheet
        cats_df = pd.DataFrame(engine.get_category_breakdown())
        cats_df.to_excel(writer, sheet_name="Categories", index=False)

    output.seek(0)
    headers = {"Content-Disposition": "attachment; filename=revenueguard_full_bi_report.xlsx"}
    return StreamingResponse(output, headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@router.get("/power-bi/dataset", dependencies=[Depends(require_permission(Permission.EXPORT_REPORTS))])
def get_power_bi_dataset(db: Session = Depends(get_db)):
    """Power BI ready tabular dataset representation with dimensional attributes."""
    query = """
    SELECT 
        o.order_number,
        o.order_date,
        c.customer_code,
        c.name AS customer_name,
        c.segment AS customer_segment,
        r.name AS region_name,
        r.country,
        p.sku AS product_sku,
        p.name AS product_name,
        cat.name AS category_name,
        oi.quantity,
        oi.unit_price,
        oi.unit_cost,
        oi.gross_revenue,
        oi.discount_amount,
        oi.net_revenue,
        oi.cogs,
        oi.profit,
        COALESCE(rf.refund_amount, 0.0) AS refund_amount,
        o.payment_method,
        o.status
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    JOIN regions r ON o.region_id = r.id
    JOIN order_items oi ON o.id = oi.order_id
    JOIN products p ON oi.product_id = p.id
    JOIN categories cat ON p.category_id = cat.id
    LEFT JOIN refunds rf ON oi.id = rf.order_item_id
    LIMIT 2500;
    """
    rows = db.execute(text(query)).mappings().all()
    return [dict(r) for r in rows]

