import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.analytics.sql_queries import (
    KPI_SUMMARY_QUERY,
    MONTHLY_REVENUE_TREND_QUERY,
    PRODUCT_PERFORMANCE_QUERY,
    CATEGORY_PERFORMANCE_QUERY,
    REGIONAL_PERFORMANCE_QUERY,
    CUSTOMER_SEGMENTATION_QUERY,
    DISCOUNT_ANALYSIS_QUERY,
    REFUND_ANALYSIS_QUERY,
    RECENT_TRANSACTIONS_QUERY
)
from backend.models import Order, OrderItem, Product, Category, Region, Customer, Refund, Discount

class AnalyticsEngine:
    """
    Enterprise-grade Python Analytics Service powered by Pandas and NumPy
    orchestrating SQL execution, data transformation, and KPI generation.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_date_bounds(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Resolves date range and previous equivalent comparison period."""
        if not end_date:
            latest_order = self.db.query(Order.order_date).order_by(Order.order_date.desc()).first()
            if latest_order and latest_order[0]:
                end_dt = latest_order[0]
            else:
                end_dt = datetime.utcnow()
        else:
            end_dt = datetime.fromisoformat(end_date.replace("Z", ""))

        if not start_date:
            start_dt = end_dt - timedelta(days=365) # default 12 months
        else:
            start_dt = datetime.fromisoformat(start_date.replace("Z", ""))

        delta = end_dt - start_dt
        prev_end_dt = start_dt
        prev_start_dt = start_dt - delta

        return (
            start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            prev_start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            prev_end_dt.strftime("%Y-%m-%d %H:%M:%S")
        )

    def calculate_dashboard_kpis(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        region_id: Optional[int] = None,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calculates 8 primary executive KPIs with period-over-period percentage changes."""
        cur_start, cur_end, prev_start, prev_end = self.get_date_bounds(start_date, end_date)

        # Pull via SQL query
        result = self.db.execute(
            text(KPI_SUMMARY_QUERY),
            {
                "start_date": cur_start,
                "end_date": cur_end,
                "prev_start_date": prev_start,
                "prev_end_date": prev_end,
                "region_id": region_id,
                "category_id": category_id
            }
        ).mappings().first()

        def make_kpi(cur_val: float, prev_val: float, is_currency: bool = True, is_pct: bool = False, reverse_sentiment: bool = False):
            cur = float(cur_val or 0.0)
            prev = float(prev_val or 0.0)
            
            if prev > 0:
                pct_change = round(((cur - prev) / prev) * 100.0, 2)
            elif prev == 0 and cur > 0:
                pct_change = 100.0
            else:
                pct_change = 0.0

            # For costs/refunds/discounts, an increase may be considered negative
            is_positive = (pct_change <= 0) if reverse_sentiment else (pct_change >= 0)

            if is_currency:
                fmt_val = f"${cur:,.2f}"
            elif is_pct:
                fmt_val = f"{cur:.1f}%"
            else:
                fmt_val = f"{int(cur):,}"

            fmt_change = f"{'+' if pct_change > 0 else ''}{pct_change:.1f}%"

            return {
                "value": cur,
                "previous_value": prev,
                "change_percentage": pct_change,
                "is_positive": is_positive,
                "formatted_value": fmt_val,
                "formatted_change": fmt_change
            }

        cur_orders = result["cur_orders"] or 0
        prev_orders = result["prev_orders"] or 0
        cur_gross = result["cur_gross_revenue"] or 0.0
        prev_gross = result["prev_gross_revenue"] or 0.0
        cur_net = result["cur_net_revenue"] or 0.0
        prev_net = result["prev_net_revenue"] or 0.0
        cur_discounts = result["cur_discounts"] or 0.0
        prev_discounts = result["prev_discounts"] or 0.0
        cur_refunds = result["cur_refunds"] or 0.0
        prev_refunds = result["prev_refunds"] or 0.0
        cur_profit = result["cur_profit"] or 0.0
        prev_profit = result["prev_profit"] or 0.0

        cur_aov = (cur_net / cur_orders) if cur_orders > 0 else 0.0
        prev_aov = (prev_net / prev_orders) if prev_orders > 0 else 0.0

        cur_margin = (cur_profit * 100.0 / cur_net) if cur_net > 0 else 0.0
        prev_margin = (prev_profit * 100.0 / prev_net) if prev_net > 0 else 0.0

        return {
            "total_revenue": make_kpi(cur_gross, prev_gross, is_currency=True),
            "net_revenue": make_kpi(cur_net, prev_net, is_currency=True),
            "total_orders": make_kpi(cur_orders, prev_orders, is_currency=False),
            "average_order_value": make_kpi(cur_aov, prev_aov, is_currency=True),
            "total_discounts": make_kpi(cur_discounts, prev_discounts, is_currency=True, reverse_sentiment=True),
            "total_refunds": make_kpi(cur_refunds, prev_refunds, is_currency=True, reverse_sentiment=True),
            "gross_profit": make_kpi(cur_profit, prev_profit, is_currency=True),
            "profit_margin": make_kpi(cur_margin, prev_margin, is_currency=False, is_pct=True)
        }

    def get_monthly_revenue_trend(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        region_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Calculates monthly revenue, profit, discounts, and refunds with growth rates."""
        cur_start, cur_end, _, _ = self.get_date_bounds(start_date, end_date)

        rows = self.db.execute(
            text(MONTHLY_REVENUE_TREND_QUERY),
            {
                "start_date": cur_start,
                "end_date": cur_end,
                "region_id": region_id
            }
        ).mappings().all()

        month_names = {
            "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
            "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
            "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
        }

        trend = []
        for r in rows:
            period = str(r["month_period"])
            parts = period.split("-")
            label = f"{month_names.get(parts[1], parts[1])} {parts[0][-2:]}" if len(parts) > 1 else period
            trend.append({
                "date": period,
                "label": label,
                "gross_revenue": round(float(r["gross_revenue"] or 0), 2),
                "net_revenue": round(float(r["net_revenue"] or 0), 2),
                "total_revenue": round(float(r["net_revenue"] or 0), 2),
                "profit": round(float(r["net_profit"] or 0), 2),
                "orders_count": int(r["orders_count"] or 0),
                "discounts": round(float(r["total_discounts"] or 0), 2),
                "refunds": round(float(r["total_refunds"] or 0), 2),
                "growth_rate": float(r["revenue_growth_rate"] or 0)
            })

        return trend

    def get_category_breakdown(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculates revenue and profit contribution by product category."""
        cur_start, cur_end, _, _ = self.get_date_bounds(start_date, end_date)

        rows = self.db.execute(
            text(CATEGORY_PERFORMANCE_QUERY),
            {"start_date": cur_start, "end_date": cur_end}
        ).mappings().all()

        return [
            {
                "category_id": int(r["category_id"]),
                "category_name": str(r["category_name"]),
                "orders_count": int(r["orders_count"] or 0),
                "units_sold": int(r["units_sold"] or 0),
                "gross_revenue": round(float(r["gross_revenue"] or 0), 2),
                "discount_amount": round(float(r["discount_amount"] or 0), 2),
                "refund_amount": round(float(r["refund_amount"] or 0), 2),
                "revenue": round(float(r["revenue"] or 0), 2),
                "profit": round(float(r["profit"] or 0), 2),
                "percentage": round(float(r["percentage"] or 0), 2),
                "profit_margin": round(float(r["profit_margin"] or 0), 2)
            }
            for r in rows
        ]

    def get_top_products(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Calculates top products ranked by net revenue using window functions."""
        cur_start, cur_end, _, _ = self.get_date_bounds(start_date, end_date)

        rows = self.db.execute(
            text(PRODUCT_PERFORMANCE_QUERY),
            {
                "start_date": cur_start,
                "end_date": cur_end,
                "category_id": category_id,
                "limit": limit
            }
        ).mappings().all()

        return [
            {
                "product_id": int(r["product_id"]),
                "sku": str(r["sku"]),
                "name": str(r["product_name"]),
                "category_name": str(r["category_name"]),
                "unit_price": round(float(r["unit_price"] or 0), 2),
                "unit_cost": round(float(r["unit_cost"] or 0), 2),
                "units_sold": int(r["units_sold"] or 0),
                "gross_revenue": round(float(r["gross_revenue"] or 0), 2),
                "discount_amount": round(float(r["discount_amount"] or 0), 2),
                "revenue": round(float(r["final_net_revenue"] or 0), 2),
                "refund_amount": round(float(r["refund_amount"] or 0), 2),
                "profit": round(float(r["profit"] or 0), 2),
                "profit_margin": round(float(r["profit_margin"] or 0), 2),
                "discount_rate": round(float(r["discount_rate"] or 0), 2),
                "refund_rate": round(float(r["refund_rate"] or 0), 2),
                "rank": int(r["revenue_rank"] or 0)
            }
            for r in rows
        ]

    def get_regional_breakdown(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculates performance across regions with discount and refund metrics."""
        cur_start, cur_end, _, _ = self.get_date_bounds(start_date, end_date)

        rows = self.db.execute(
            text(REGIONAL_PERFORMANCE_QUERY),
            {"start_date": cur_start, "end_date": cur_end}
        ).mappings().all()

        return [
            {
                "region_id": int(r["region_id"]),
                "region_name": str(r["region_name"]),
                "country": str(r["country"]),
                "state": str(r["state"] or ""),
                "city": str(r["city"] or ""),
                "code": str(r["code"]),
                "orders_count": int(r["orders_count"] or 0),
                "gross_revenue": round(float(r["gross_revenue"] or 0), 2),
                "discount_amount": round(float(r["discount_amount"] or 0), 2),
                "refund_amount": round(float(r["refund_amount"] or 0), 2),
                "revenue": round(float(r["revenue"] or 0), 2),
                "profit": round(float(r["profit"] or 0), 2),
                "profit_margin": round(float(r["profit_margin"] or 0), 2),
                "refund_rate": round(float(r["refund_rate"] or 0), 2),
                "discount_rate": round(float(r["discount_rate"] or 0), 2)
            }
            for r in rows
        ]

    def get_customer_segments(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculates metrics segmented by customer classification."""
        cur_start, cur_end, _, _ = self.get_date_bounds(start_date, end_date)

        rows = self.db.execute(
            text(CUSTOMER_SEGMENTATION_QUERY),
            {"start_date": cur_start, "end_date": cur_end}
        ).mappings().all()

        return [
            {
                "segment": str(r["segment"]),
                "customers_count": int(r["customers_count"] or 0),
                "orders_count": int(r["orders_count"] or 0),
                "revenue": round(float(r["revenue"] or 0), 2),
                "profit": round(float(r["profit"] or 0), 2),
                "refund_amount": round(float(r["refund_amount"] or 0), 2),
                "average_order_value": round(float(r["average_order_value"] or 0), 2),
                "repeat_rate": round(float(r["repeat_rate"] or 0), 2)
            }
            for r in rows
        ]

    def get_discount_analysis(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Evaluates discount types, codes, usage and revenue erosion."""
        cur_start, cur_end, _, _ = self.get_date_bounds(start_date, end_date)

        rows = self.db.execute(
            text(DISCOUNT_ANALYSIS_QUERY),
            {"start_date": cur_start, "end_date": cur_end}
        ).mappings().all()

        return [
            {
                "discount_type": str(r["discount_type"]),
                "discount_code": str(r["discount_code"] or "STANDARD"),
                "orders_count": int(r["orders_count"] or 0),
                "avg_discount_pct": float(r["avg_discount_pct"] or 0),
                "total_discount": float(r["total_discount"] or 0),
                "revenue_before": float(r["revenue_before"] or 0),
                "revenue_after": float(r["revenue_after"] or 0),
                "profit_impact": float(r["profit_impact"] or 0)
            }
            for r in rows
        ]

    def get_refund_reasons(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Categorizes refund reasons, financial leakage, and proportion."""
        cur_start, cur_end, _, _ = self.get_date_bounds(start_date, end_date)

        rows = self.db.execute(
            text(REFUND_ANALYSIS_QUERY),
            {"start_date": cur_start, "end_date": cur_end}
        ).mappings().all()

        return [
            {
                "reason": str(r["reason"]),
                "count": int(r["count"] or 0),
                "total_amount": float(r["total_amount"] or 0),
                "avg_amount": float(r["avg_amount"] or 0),
                "percentage": float(r["percentage"] or 0)
            }
            for r in rows
        ]

    def get_recent_transactions(
        self,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetches detailed transactions with order items, discounts, and refund status."""
        search_param = f"%{search}%" if search else None

        rows = self.db.execute(
            text(RECENT_TRANSACTIONS_QUERY),
            {"search": search_param, "limit": limit, "offset": offset}
        ).mappings().all()

        return [
            {
                "order_id": int(r["order_id"]),
                "order_number": str(r["order_number"]),
                "order_date": str(r["order_date"]),
                "customer_name": str(r["customer_name"]),
                "customer_segment": str(r["customer_segment"]),
                "product_summary": str(r["product_summary"] or "Multiple items"),
                "gross_revenue": float(r["gross_revenue"] or 0),
                "discount_amount": float(r["discount_amount"] or 0),
                "refund_amount": float(r["refund_amount"] or 0),
                "net_amount": float(r["net_amount"] or 0),
                "status": str(r["status"]),
                "payment_method": str(r["payment_method"])
            }
            for r in rows
        ]
