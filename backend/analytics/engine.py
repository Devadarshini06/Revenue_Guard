import sys
from pathlib import Path

# Ensure project root is in sys.path when running script directly
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
        """Resolves date range and previous equivalent comparison period with end-of-day precision."""
        if not end_date:
            latest_order = self.db.query(Order.order_date).order_by(Order.order_date.desc()).first()
            if latest_order and latest_order[0]:
                end_dt = latest_order[0]
            else:
                end_dt = datetime.utcnow()
        else:
            clean_end = end_date.replace("Z", "")
            if len(clean_end) == 10:
                end_dt = datetime.fromisoformat(clean_end).replace(hour=23, minute=59, second=59)
            else:
                end_dt = datetime.fromisoformat(clean_end)

        if not start_date:
            start_dt = end_dt - timedelta(days=365) # default 12 months
        else:
            clean_start = start_date.replace("Z", "")
            if len(clean_start) == 10:
                start_dt = datetime.fromisoformat(clean_start).replace(hour=0, minute=0, second=0)
            else:
                start_dt = datetime.fromisoformat(clean_start)

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
        region_id: Optional[int] = None,
        grain: str = "monthly"
    ) -> List[Dict[str, Any]]:
        """Calculates monthly or quarterly revenue, profit, discounts, and refunds with growth rates."""
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

        if grain == "quarterly":
            quarterly = {}
            for t in trend:
                year, month = t["date"].split("-")
                q = (int(month) - 1) // 3 + 1
                q_key = f"{year}-Q{q}"
                q_label = f"Q{q} '{year[-2:]}"
                if q_key not in quarterly:
                    quarterly[q_key] = {
                        "date": q_key,
                        "label": q_label,
                        "gross_revenue": 0.0,
                        "net_revenue": 0.0,
                        "total_revenue": 0.0,
                        "profit": 0.0,
                        "orders_count": 0,
                        "discounts": 0.0,
                        "refunds": 0.0,
                    }
                quarterly[q_key]["gross_revenue"] += t["gross_revenue"]
                quarterly[q_key]["net_revenue"] += t["net_revenue"]
                quarterly[q_key]["total_revenue"] += t["total_revenue"]
                quarterly[q_key]["profit"] += t["profit"]
                quarterly[q_key]["orders_count"] += t["orders_count"]
                quarterly[q_key]["discounts"] += t["discounts"]
                quarterly[q_key]["refunds"] += t["refunds"]

            q_list = list(quarterly.values())
            for idx, q_data in enumerate(q_list):
                prev_net = q_list[idx - 1]["net_revenue"] if idx > 0 else None
                if prev_net and prev_net > 0:
                    q_data["growth_rate"] = round(((q_data["net_revenue"] - prev_net) * 100.0 / prev_net), 2)
                else:
                    q_data["growth_rate"] = 0.0
                q_data["gross_revenue"] = round(q_data["gross_revenue"], 2)
                q_data["net_revenue"] = round(q_data["net_revenue"], 2)
                q_data["total_revenue"] = round(q_data["total_revenue"], 2)
                q_data["profit"] = round(q_data["profit"], 2)
                q_data["discounts"] = round(q_data["discounts"], 2)
                q_data["refunds"] = round(q_data["refunds"], 2)
            return q_list

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


if __name__ == "__main__":
    from backend.database import SessionLocal

    print("=" * 80)
    print("  REVENUEGUARD ENTERPRISE ANALYTICS ENGINE")
    print("  Executing high-performance SQL + Pandas data transformations...")
    print("=" * 80)

    db = SessionLocal()
    try:
        engine = AnalyticsEngine(db)

        # 1. Executive Dashboard KPIs
        print("\n[1] CALCULATING EXECUTIVE KPIS (Trailing 12 Months vs Prior Period)...")
        kpis = engine.calculate_dashboard_kpis()
        for key, data in kpis.items():
            val_str = data["formatted_value"]
            pct_str = data["formatted_change"]
            print(f"  • {key.replace('_', ' ').title():<22}: {val_str:>14}  ({pct_str} vs prior)")

        # 2. Monthly Revenue Trend
        print("\n[2] MONTHLY REVENUE & PROFIT TREND (Latest 6 Months):")
        trends = engine.get_monthly_revenue_trend()
        print(f"  {'Month':<10} | {'Gross Revenue':>14} | {'Net Revenue':>14} | {'Gross Profit':>14} | {'Orders':>8}")
        print("  " + "-" * 72)
        for t in trends[-6:]:  # show latest 6 months
            print(f"  {t['label']:<10} | ${t['gross_revenue']:>13,.2f} | ${t['net_revenue']:>13,.2f} | ${t['profit']:>13,.2f} | {t['orders_count']:>8,}")

        # 3. Top Products by Revenue
        print("\n[3] TOP 5 PERFORMING PRODUCTS:")
        top_products = engine.get_top_products(limit=5)
        print(f"  {'Product Name':<32} | {'Category':<15} | {'Units Sold':>10} | {'Revenue':>12}")
        print("  " + "-" * 78)
        for p in top_products:
            print(f"  {p['name'][:30]:<32} | {p['category_name'][:13]:<15} | {p['units_sold']:>10,} | ${p['revenue']:>11,.2f}")

        # 4. Category Breakdown
        print("\n[4] REVENUE CONTRIBUTION BY CATEGORY:")
        categories = engine.get_category_breakdown()
        for c in categories:
            bar = "█" * int(c["percentage"] / 2.5)
            print(f"  • {c['category_name']:<20}: ${c['revenue']:>12,.2f} ({c['percentage']:>5.1f}%) {bar}")

        # 5. Discount & Refund Leakage
        print("\n[5] FINANCIAL DEDUCTIONS & LEAKAGE:")
        discount_items = engine.get_discount_analysis()
        total_discount_leakage = sum(d["total_discount"] for d in discount_items)
        refunds = engine.get_refund_reasons()
        total_refund_leakage = sum(r["total_amount"] for r in refunds)
        print(f"  • Total Discount Leakage : ${total_discount_leakage:,.2f} across {len(discount_items)} discount strategies")
        print(f"  • Total Refund Leakage   : ${total_refund_leakage:,.2f}")
        if refunds:
            print(f"  • Primary Refund Driver  : {refunds[0]['reason']} (${refunds[0]['total_amount']:,.2f} - {refunds[0]['percentage']:.1f}% of refunds)")

        # 6. Recent Transactions Sample
        print("\n[6] RECENT TRANSACTIONS (Top 3 Records):")
        txs = engine.get_recent_transactions(limit=3)
        for tx in txs:
            print(f"  • [{tx['order_number']}] {tx['order_date'][:10]} | {tx['customer_name']} ({tx['customer_segment']}) -> Net: ${tx['net_amount']:,.2f} | Status: {tx['status']}")

        print("\n" + "=" * 80)
        print("  ✓ Analytics Engine executed successfully. All metrics computed without errors.")
        print("=" * 80)

    finally:
        db.close()
