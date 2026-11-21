import unittest
import sys
from pathlib import Path
from sqlalchemy import text

# Ensure project root in sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import SessionLocal
from backend.analytics.engine import AnalyticsEngine


class TestAnalyticsValidation(unittest.TestCase):
    """
    Comprehensive Analytical Query & Engine Validation Test Suite.
    Executes assertions against ground-truth database records to ensure
    no Cartesian fan-out, correct date filtering, and exact financial balance.
    """

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.engine = AnalyticsEngine(cls.db)

        # Baseline Ground Truth computed via simple direct single-table queries
        cls.gt_gross = cls.db.execute(text("SELECT SUM(gross_revenue) FROM order_items")).scalar()
        cls.gt_discounts = cls.db.execute(text("SELECT SUM(discount_amount) FROM order_items")).scalar()
        cls.gt_cogs = cls.db.execute(text("SELECT SUM(cogs) FROM order_items")).scalar()
        cls.gt_refunds = cls.db.execute(text("SELECT SUM(refund_amount) FROM refunds")).scalar()
        cls.gt_orders = cls.db.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        cls.gt_net = cls.gt_gross - cls.gt_discounts - cls.gt_refunds
        cls.gt_profit = cls.gt_net - cls.gt_cogs
        cls.gt_margin = (cls.gt_profit * 100.0 / cls.gt_net) if cls.gt_net > 0 else 0.0
        cls.gt_aov = cls.gt_net / cls.gt_orders if cls.gt_orders > 0 else 0.0

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_ground_truth_baseline_sanity(self):
        """Verifies database contains expected populated records."""
        self.assertEqual(self.gt_orders, 5200)
        self.assertAlmostEqual(self.gt_gross, 38625502.00, places=2)
        self.assertAlmostEqual(self.gt_discounts, 2342815.06, places=2)
        self.assertAlmostEqual(self.gt_refunds, 1261629.33, places=2)
        self.assertAlmostEqual(self.gt_net, 35021057.61, places=2)
        self.assertAlmostEqual(self.gt_cogs, 21138510.00, places=2)
        self.assertAlmostEqual(self.gt_profit, 13882547.61, places=2)

    def test_02_kpi_summary_query_no_fanout(self):
        """Validates that KPI_SUMMARY_QUERY does NOT duplicate refunds via Cartesian join."""
        kpis = self.engine.calculate_dashboard_kpis(start_date="2020-01-01", end_date="2030-01-01")

        total_rev = kpis["total_revenue"]["value"]
        total_disc = kpis["total_discounts"]["value"]
        total_ref = kpis["total_refunds"]["value"]
        net_rev = kpis["net_revenue"]["value"]
        profit = kpis["gross_profit"]["value"]
        orders = kpis["total_orders"]["value"]
        aov = kpis["average_order_value"]["value"]
        margin = kpis["profit_margin"]["value"]

        # Assert exact matches to ground truth
        self.assertAlmostEqual(total_rev, self.gt_gross, places=2)
        self.assertAlmostEqual(total_disc, self.gt_discounts, places=2)
        # CRITICAL ASSERTION: Refund must equal $1,261,629.33, NOT the buggy $2,404,164.54
        self.assertAlmostEqual(total_ref, self.gt_refunds, places=2)
        self.assertAlmostEqual(net_rev, self.gt_net, places=2)
        self.assertAlmostEqual(profit, self.gt_profit, places=2)
        self.assertEqual(orders, self.gt_orders)
        self.assertAlmostEqual(aov, self.gt_aov, places=2)
        self.assertAlmostEqual(margin, round(self.gt_margin, 1), places=1)

    def test_03_monthly_aggregation_reconciliation(self):
        """Validates that summing all monthly trend points equals the overall ground truth."""
        trends = self.engine.get_monthly_revenue_trend(start_date="2020-01-01", end_date="2030-01-01", grain="monthly")

        self.assertGreater(len(trends), 0)
        sum_gross = sum(t["gross_revenue"] for t in trends)
        sum_discounts = sum(t["discounts"] for t in trends)
        sum_refunds = sum(t["refunds"] for t in trends)
        sum_net = sum(t["net_revenue"] for t in trends)
        sum_profit = sum(t["profit"] for t in trends)
        sum_orders = sum(t["orders_count"] for t in trends)

        self.assertAlmostEqual(sum_gross, self.gt_gross, places=2)
        self.assertAlmostEqual(sum_discounts, self.gt_discounts, places=2)
        self.assertAlmostEqual(sum_refunds, self.gt_refunds, places=2)
        self.assertAlmostEqual(sum_net, self.gt_net, places=2)
        self.assertAlmostEqual(sum_profit, self.gt_profit, places=2)
        self.assertEqual(sum_orders, self.gt_orders)

    def test_04_quarterly_aggregation(self):
        """Validates quarterly grain aggregation logic and growth rate."""
        quarterly = self.engine.get_monthly_revenue_trend(start_date="2020-01-01", end_date="2030-01-01", grain="quarterly")

        self.assertGreater(len(quarterly), 0)
        sum_q_net = sum(q["net_revenue"] for q in quarterly)
        sum_q_profit = sum(q["profit"] for q in quarterly)

        self.assertAlmostEqual(sum_q_net, self.gt_net, places=2)
        self.assertAlmostEqual(sum_q_profit, self.gt_profit, places=2)

    def test_05_category_breakdown_reconciliation(self):
        """Validates that category breakdown totals sum to 100% and match ground truth."""
        categories = self.engine.get_category_breakdown(start_date="2020-01-01", end_date="2030-01-01")

        self.assertEqual(len(categories), 5)
        sum_cat_gross = sum(c["gross_revenue"] for c in categories)
        sum_cat_net = sum(c["revenue"] for c in categories)
        sum_cat_refunds = sum(c["refund_amount"] for c in categories)
        sum_cat_profit = sum(c["profit"] for c in categories)
        sum_cat_pct = sum(c["percentage"] for c in categories)

        self.assertAlmostEqual(sum_cat_gross, self.gt_gross, places=2)
        self.assertAlmostEqual(sum_cat_net, self.gt_net, places=2)
        self.assertAlmostEqual(sum_cat_refunds, self.gt_refunds, places=2)
        self.assertAlmostEqual(sum_cat_profit, self.gt_profit, places=2)
        self.assertAlmostEqual(sum_cat_pct, 100.0, places=1)

    def test_06_regional_breakdown_reconciliation(self):
        """Validates regional performance metrics reconcile exactly to company totals."""
        regions = self.engine.get_regional_breakdown(start_date="2020-01-01", end_date="2030-01-01")

        self.assertEqual(len(regions), 8)
        sum_reg_net = sum(r["revenue"] for r in regions)
        sum_reg_profit = sum(r["profit"] for r in regions)
        sum_reg_refunds = sum(r["refund_amount"] for r in regions)

        self.assertAlmostEqual(sum_reg_net, self.gt_net, places=2)
        self.assertAlmostEqual(sum_reg_profit, self.gt_profit, places=2)
        self.assertAlmostEqual(sum_reg_refunds, self.gt_refunds, places=2)

    def test_07_customer_segmentation_reconciliation(self):
        """Validates customer segmentation revenue sums to total net revenue."""
        segments = self.engine.get_customer_segments(start_date="2020-01-01", end_date="2030-01-01")

        self.assertEqual(len(segments), 4) # Enterprise, Mid-Market, SMB, Direct Consumer
        sum_seg_net = sum(s["revenue"] for s in segments)
        sum_seg_refunds = sum(s["refund_amount"] for s in segments)

        self.assertAlmostEqual(sum_seg_net, self.gt_net, places=2)
        self.assertAlmostEqual(sum_seg_refunds, self.gt_refunds, places=2)

    def test_08_empty_date_boundary_filtering(self):
        """Validates that out-of-range dates return exactly 0 metrics with no stray items."""
        empty_kpis = self.engine.calculate_dashboard_kpis(start_date="2010-01-01", end_date="2010-01-02")
        self.assertEqual(empty_kpis["total_orders"]["value"], 0)
        self.assertEqual(empty_kpis["total_revenue"]["value"], 0.0)
        self.assertEqual(empty_kpis["net_revenue"]["value"], 0.0)
        self.assertEqual(empty_kpis["total_refunds"]["value"], 0.0)

        empty_prods = self.engine.get_top_products(start_date="2010-01-01", end_date="2010-01-02")
        self.assertTrue(all(p["units_sold"] == 0 for p in empty_prods))

    def test_09_discount_and_refund_reason_analysis(self):
        """Validates discount strategies and refund reasons distribution."""
        discounts = self.engine.get_discount_analysis(start_date="2020-01-01", end_date="2030-01-01")
        self.assertGreater(len(discounts), 0)
        total_disc_table = sum(d["total_discount"] for d in discounts)
        self.assertAlmostEqual(total_disc_table, self.gt_discounts, places=2)

        refund_reasons = self.engine.get_refund_reasons(start_date="2020-01-01", end_date="2030-01-01")
        self.assertGreater(len(refund_reasons), 0)
        sum_reasons_pct = sum(r["percentage"] for r in refund_reasons)
        self.assertAlmostEqual(sum_reasons_pct, 100.0, places=1)
        sum_reasons_amt = sum(r["total_amount"] for r in refund_reasons)
        self.assertAlmostEqual(sum_reasons_amt, self.gt_refunds, places=2)


if __name__ == "__main__":
    unittest.main()
