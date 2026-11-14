from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.analytics.engine import AnalyticsEngine

class InsightGenerator:
    """
    Synthesizes computed metrics from the database and AnalyticsEngine
    to generate data-backed, dynamic executive business insights.
    """

    def __init__(self, db: Session):
        self.db = db
        self.engine = AnalyticsEngine(db)

    def generate_insights(
        self,
        start_date: str = None,
        end_date: str = None,
        region_id: int = None,
        category_id: int = None
    ) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []

        # 1. Evaluate KPIs and Period Growth
        kpis = self.engine.calculate_dashboard_kpis(start_date, end_date, region_id, category_id)
        rev_kpi = kpis.get("net_revenue", {})
        growth_pct = rev_kpi.get("change_percentage", 0.0)
        net_rev_val = rev_kpi.get("value", 0.0)
        margin_kpi = kpis.get("profit_margin", {})
        margin_pct = margin_kpi.get("value", 0.0)
        margin_change = margin_kpi.get("change_percentage", 0.0)

        # Revenue velocity insight
        if growth_pct > 0:
            insights.append({
                "id": "ins-rev-growth",
                "type": "success",
                "title": "Positive Revenue Velocity",
                "description": f"Net realized revenue expanded by {growth_pct:.1f}% compared to the prior period, reaching {rev_kpi.get('formatted_value')}.",
                "metric_value": f"+{growth_pct:.1f}%",
                "recommendation": "Maintain inventory depth for leading stock keeping units to prevent stock-outs during demand peaks.",
                "category": "Revenue"
            })
        elif growth_pct < 0:
            insights.append({
                "id": "ins-rev-drop",
                "type": "danger",
                "title": "Revenue Contraction Detected",
                "description": f"Net revenue contracted by {abs(growth_pct):.1f}% against the baseline period, requiring commercial review.",
                "metric_value": f"{growth_pct:.1f}%",
                "recommendation": "Review enterprise contract pipeline and inspect conversion drop-offs in key sales territories.",
                "category": "Revenue"
            })

        # Profit margin health
        if margin_pct < 25.0:
            insights.append({
                "id": "ins-margin-warning",
                "type": "warning",
                "title": "Compressed Gross Margin Threshold",
                "description": f"Current portfolio profit margin stands at {margin_pct:.1f}%, which is below the benchmark target of 30.0%.",
                "metric_value": f"{margin_pct:.1f}% Margin",
                "recommendation": "Audit vendor procurement costs and trim promotional discount allowances on low-margin SKUs.",
                "category": "Profitability"
            })
        else:
            insights.append({
                "id": "ins-margin-healthy",
                "type": "success",
                "title": "Strong Margin Protection",
                "description": f"Gross margin performance is resilient at {margin_pct:.1f}%, sustaining solid net unit economics.",
                "metric_value": f"{margin_pct:.1f}% Margin",
                "recommendation": "Reinvest surplus operating cash flows into customer acquisition and top-tier product lines.",
                "category": "Profitability"
            })

        # 2. Evaluate Products (High revenue but low margin / excessive discounting)
        products = self.engine.get_top_products(start_date, end_date, category_id, limit=20)
        if products:
            # High revenue, low margin anomaly
            for p in products[:5]:
                if p["revenue"] > (net_rev_val * 0.05) and p["profit_margin"] < 18.0:
                    insights.append({
                        "id": f"ins-prod-margin-{p['product_id']}",
                        "type": "warning",
                        "title": f"High Volume / Thin Margin Alert: {p['name']}",
                        "description": f"Product '{p['name']}' generated ${p['revenue']:,.2f} in sales but delivers an underperforming profit margin of only {p['profit_margin']:.1f}% (Discount rate: {p['discount_rate']:.1f}%).",
                        "metric_value": f"{p['profit_margin']:.1f}% margin",
                        "recommendation": f"Calibrate pricing structure or establish a maximum coupon discount ceiling for {p['sku']}.",
                        "category": "Product"
                    })
                    break

            # Product with high refund rate
            high_refund_prods = [p for p in products if p["refund_rate"] >= 5.0 and p["units_sold"] >= 10]
            if high_refund_prods:
                hr_p = high_refund_prods[0]
                insights.append({
                    "id": f"ins-prod-refund-{hr_p['product_id']}",
                    "type": "danger",
                    "title": f"Elevated Refund Leakage on {hr_p['name']}",
                    "description": f"'{hr_p['name']}' exhibits an abnormal refund rate of {hr_p['refund_rate']:.1f}%, totaling ${hr_p['refund_amount']:,.2f} in customer clawbacks.",
                    "metric_value": f"{hr_p['refund_rate']:.1f}% Refund Rate",
                    "recommendation": "Conduct quality control audit and review customer feedback tickets regarding physical defects or shipping damage.",
                    "category": "Refund"
                })

        # 3. Category Concentration Insight
        categories = self.engine.get_category_breakdown(start_date, end_date)
        if categories:
            top_cat = categories[0]
            if top_cat["percentage"] >= 35.0:
                insights.append({
                    "id": f"ins-cat-concentration-{top_cat['category_id']}",
                    "type": "info",
                    "title": f"Category Concentration: {top_cat['category_name']}",
                    "description": f"'{top_cat['category_name']}' represents {top_cat['percentage']:.1f}% of aggregate enterprise revenue (${top_cat['revenue']:,.2f}).",
                    "metric_value": f"{top_cat['percentage']:.1f}% of Total",
                    "recommendation": "Diversify marketing spend across secondary categories to reduce revenue reliance on a single segment.",
                    "category": "Revenue"
                })

        # 4. Regional Performance Variation
        regions = self.engine.get_regional_breakdown(start_date, end_date)
        if len(regions) >= 2:
            top_reg = regions[0]
            low_reg = regions[-1]
            if top_reg["revenue"] > 0:
                insights.append({
                    "id": f"ins-reg-top-{top_reg['region_id']}",
                    "type": "info",
                    "title": f"Dominant Regional Hub: {top_reg['region_name']}",
                    "description": f"{top_reg['region_name']} leads territorial performance with ${top_reg['revenue']:,.2f} in sales and a healthy {top_reg['profit_margin']:.1f}% profit margin.",
                    "metric_value": f"${top_reg['revenue']:,.2f}",
                    "recommendation": f"Scale regional marketing campaigns in {top_reg['region_name']} while examining under-indexing in {low_reg['region_name']}.",
                    "category": "Regional"
                })

        # 5. Discounting Impact Evaluation
        discounts = self.engine.get_discount_analysis(start_date, end_date)
        if discounts:
            total_disc_sum = sum(d["total_discount"] for d in discounts)
            if total_disc_sum > 0 and net_rev_val > 0:
                disc_ratio = (total_disc_sum / (net_rev_val + total_disc_sum)) * 100.0
                if disc_ratio > 10.0:
                    insights.append({
                        "id": "ins-excess-discounts",
                        "type": "warning",
                        "title": "Aggressive Promotional Discounting",
                        "description": f"Discounts represent {disc_ratio:.1f}% of gross book value (${total_disc_sum:,.2f}), compressing overall gross profit margins.",
                        "metric_value": f"{disc_ratio:.1f}% of Gross",
                        "recommendation": "Shift from sitewide percentage markdowns to minimum-order-value (MOV) tier requirements.",
                        "category": "Discount"
                    })

        # 6. Refund Reasons & Quality Leakage
        refunds = self.engine.get_refund_reasons(start_date, end_date)
        if refunds:
            top_reason = refunds[0]
            insights.append({
                "id": "ins-refund-driver",
                "type": "danger" if top_reason["percentage"] > 30 else "warning",
                "title": f"Primary Refund Driver: {top_reason['reason']}",
                "description": f"'{top_reason['reason']}' accounts for {top_reason['percentage']:.1f}% of all refund claims (${top_reason['total_amount']:,.2f}).",
                "metric_value": f"{top_reason['percentage']:.1f}% of Refunds",
                "recommendation": f"Coordinate with logistics and QA engineering to remediate causes tied to '{top_reason['reason']}'.",
                "category": "Refund"
            })

        return insights

