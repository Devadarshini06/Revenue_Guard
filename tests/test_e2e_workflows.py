import unittest
from backend.main import app
from tests.asgi_client import ASGITestClient
import backend.schemas as schemas


class TestEndToEndWorkflows(unittest.TestCase):
    """
    Milestone 6: Comprehensive End-to-End System Validation & Business Workflow Test Suite.
    Validates user workflows A through K covering analytics, data integrity, security,
    export streaming, and health checks across the live RevenueGuard application.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = ASGITestClient(app)

    # -------------------------------------------------------------------------
    # Workflow A – Executive Dashboard
    # -------------------------------------------------------------------------
    def test_workflow_a_executive_dashboard(self):
        # 1. Verify default KPI cards (Trailing 12 Months)
        res_kpis = self.client.get("/api/overview/kpis")
        self.assertEqual(res_kpis.status_code, 200)
        kpi_data = res_kpis.json()
        self.assertEqual(int(kpi_data["total_orders"]["value"]), 3822)
        self.assertAlmostEqual(kpi_data["total_revenue"]["value"], 28488467.00, places=2)
        self.assertAlmostEqual(kpi_data["net_revenue"]["value"], 25900147.21, places=2)
        self.assertAlmostEqual(kpi_data["gross_profit"]["value"], 10210727.21, places=2)
        self.assertAlmostEqual(kpi_data["profit_margin"]["value"], 39.42, places=1)
        self.assertAlmostEqual(kpi_data["average_order_value"]["value"], 6776.60, places=1)

        # 2. Verify all-time scope (5,200 orders)
        res_all = self.client.get("/api/overview/kpis", params={"start_date": "2020-01-01", "end_date": "2030-01-01"})
        self.assertEqual(res_all.status_code, 200)
        all_data = res_all.json()
        self.assertEqual(int(all_data["total_orders"]["value"]), 5200)
        self.assertAlmostEqual(all_data["total_revenue"]["value"], 38625502.00, places=2)
        self.assertAlmostEqual(all_data["net_revenue"]["value"], 35021057.61, places=2)
        self.assertAlmostEqual(all_data["gross_profit"]["value"], 13882547.61, places=2)

        # 3. Verify category breakdown reconciles to Net Revenue
        res_cat = self.client.get("/api/overview/category-breakdown")
        self.assertEqual(res_cat.status_code, 200)
        cat_data = res_cat.json()
        sum_cat_rev = sum(c["revenue"] for c in cat_data)
        self.assertAlmostEqual(sum_cat_rev, kpi_data["net_revenue"]["value"], places=2)

        # 4. Verify regional sales reconciles to Net Revenue
        res_reg = self.client.get("/api/overview/regional-sales")
        self.assertEqual(res_reg.status_code, 200)
        reg_data = res_reg.json()
        sum_reg_rev = sum(r["revenue"] for r in reg_data)
        self.assertAlmostEqual(sum_reg_rev, kpi_data["net_revenue"]["value"], places=2)

        # 5. Verify recent transactions & insights
        res_tx = self.client.get("/api/overview/recent-transactions", params={"limit": 10})
        self.assertEqual(res_tx.status_code, 200)
        self.assertEqual(len(res_tx.json()), 10)

        res_ins = self.client.get("/api/overview/insights")
        self.assertEqual(res_ins.status_code, 200)
        self.assertGreater(len(res_ins.json()), 0)

    # -------------------------------------------------------------------------
    # Workflow B – Revenue Analysis
    # -------------------------------------------------------------------------
    def test_workflow_b_revenue_analysis(self):
        # 1. Summary
        res_sum = self.client.get("/api/revenue/summary")
        self.assertEqual(res_sum.status_code, 200)
        d_sum = res_sum.json()
        self.assertAlmostEqual(d_sum["gross_revenue"]["value"], 28488467.00, places=2)
        self.assertAlmostEqual(d_sum["net_revenue"]["value"], 25900147.21, places=2)
        self.assertAlmostEqual(d_sum["discounts"]["value"], 1670808.06, places=2)
        self.assertAlmostEqual(d_sum["refunds"]["value"], 917511.73, places=2)

        # 2. Monthly Trends sum to Net Revenue
        res_monthly = self.client.get("/api/revenue/trends", params={"grain": "monthly"})
        self.assertEqual(res_monthly.status_code, 200)
        monthly_pts = res_monthly.json()
        self.assertGreater(len(monthly_pts), 0)
        sum_monthly_net = sum(p["net_revenue"] for p in monthly_pts)
        self.assertAlmostEqual(sum_monthly_net, 25900147.21, places=2)

        # 3. Quarterly Grain view
        res_quarterly = self.client.get("/api/revenue/trends", params={"grain": "quarterly"})
        self.assertEqual(res_quarterly.status_code, 200)
        quarterly_pts = res_quarterly.json()
        self.assertGreater(len(quarterly_pts), 0)
        for pt in quarterly_pts:
            self.assertIn("growth_rate", pt)

        # 4. Slices: by category, by region, by product
        self.assertEqual(self.client.get("/api/revenue/by-category").status_code, 200)
        self.assertEqual(self.client.get("/api/revenue/by-region").status_code, 200)
        self.assertEqual(self.client.get("/api/revenue/by-product").status_code, 200)

    # -------------------------------------------------------------------------
    # Workflow C – Sales Performance
    # -------------------------------------------------------------------------
    def test_workflow_c_sales_performance(self):
        res_sales = self.client.get("/api/sales/summary")
        self.assertEqual(res_sales.status_code, 200)
        d_sales = res_sales.json()
        self.assertEqual(int(d_sales["total_orders"]), 3822)
        # In sales summary, total_sales is Gross Revenue minus Discounts ($26,817,658.94)
        self.assertAlmostEqual(d_sales["total_sales"], 26817658.94, places=2)

        # Payment methods: sum to 100% and provide Recharts dual keys
        res_pm = self.client.get("/api/sales/payment-methods")
        self.assertEqual(res_pm.status_code, 200)
        pm_data = res_pm.json()
        self.assertGreater(len(pm_data), 0)
        total_pct = sum(item["percentage"] for item in pm_data)
        self.assertAlmostEqual(total_pct, 100.0, places=1)
        for item in pm_data:
            self.assertIn("name", item)
            self.assertIn("value", item)
            self.assertIn("payment_method", item)
            self.assertIn("total_amount", item)

        # Sales transactions list
        res_tx = self.client.get("/api/sales/transactions", params={"limit": 15})
        self.assertEqual(res_tx.status_code, 200)
        self.assertEqual(len(res_tx.json()), 15)

    # -------------------------------------------------------------------------
    # Workflow D – Discount Analysis
    # -------------------------------------------------------------------------
    def test_workflow_d_discount_analysis(self):
        res_disc = self.client.get("/api/discounts/summary")
        self.assertEqual(res_disc.status_code, 200)
        d_disc = res_disc.json()
        self.assertAlmostEqual(d_disc["total_discounts"], 1670808.06, places=2)
        self.assertAlmostEqual(d_disc["average_discount_percentage"], 16.56, places=1)

        res_types = self.client.get("/api/discounts/by-type")
        self.assertEqual(res_types.status_code, 200)
        self.assertGreater(len(res_types.json()), 0)

        res_cat = self.client.get("/api/discounts/by-category")
        self.assertEqual(res_cat.status_code, 200)
        self.assertGreater(len(res_cat.json()), 0)

        res_high = self.client.get("/api/discounts/high-discount-orders", params={"limit": 10})
        self.assertEqual(res_high.status_code, 200)
        self.assertLessEqual(len(res_high.json()), 10)

    # -------------------------------------------------------------------------
    # Workflow E – Refund Analysis
    # -------------------------------------------------------------------------
    def test_workflow_e_refund_analysis(self):
        res_ref = self.client.get("/api/refunds/summary")
        self.assertEqual(res_ref.status_code, 200)
        d_ref = res_ref.json()
        self.assertGreater(d_ref["total_refund_amount"], 900000.00)
        self.assertAlmostEqual(d_ref["refund_rate"], 3.19, places=1)

        res_reasons = self.client.get("/api/refunds/reasons")
        self.assertEqual(res_reasons.status_code, 200)
        self.assertGreater(len(res_reasons.json()), 0)

        res_cat_ref = self.client.get("/api/refunds/by-category")
        self.assertEqual(res_cat_ref.status_code, 200)
        self.assertGreater(len(res_cat_ref.json()), 0)

        res_high_ref = self.client.get("/api/refunds/high-refund-products", params={"limit": 5})
        self.assertEqual(res_high_ref.status_code, 200)
        self.assertLessEqual(len(res_high_ref.json()), 5)

    # -------------------------------------------------------------------------
    # Workflow F – Profitability Analysis
    # -------------------------------------------------------------------------
    def test_workflow_f_profitability_analysis(self):
        res_prof = self.client.get("/api/profitability/summary")
        self.assertEqual(res_prof.status_code, 200)
        d_prof = res_prof.json()
        self.assertAlmostEqual(d_prof["cost_of_goods_sold"], 15689420.00, places=2)
        self.assertAlmostEqual(d_prof["gross_profit"], 10210727.21, places=2)
        self.assertAlmostEqual(d_prof["profit_margin"], 39.42, places=1)
        # Verify formula: Net Revenue - COGS == Gross Profit
        self.assertAlmostEqual(d_prof["net_revenue"] - d_prof["cost_of_goods_sold"], d_prof["gross_profit"], places=2)

        # Quadrant classification
        res_quad = self.client.get("/api/profitability/product-quadrant")
        self.assertEqual(res_quad.status_code, 200)
        quad_data = res_quad.json()
        valid_quadrants = {
            "Star (High Revenue, High Margin)",
            "Workhorse (High Revenue, Low Margin)",
            "Niche Opportunity (Low Revenue, High Margin)",
            "Underperformer (Low Revenue, Low Margin)",
        }
        for q in quad_data:
            self.assertIn(q["classification"], valid_quadrants)

        # Monthly trends
        res_trends = self.client.get("/api/profitability/monthly-trends")
        self.assertEqual(res_trends.status_code, 200)
        self.assertGreater(len(res_trends.json()), 0)

    # -------------------------------------------------------------------------
    # Workflow G – Product and Customer Insights
    # -------------------------------------------------------------------------
    def test_workflow_g_product_and_customer_insights(self):
        # Product performance
        res_perf = self.client.get("/api/products/performance", params={"limit": 10})
        self.assertEqual(res_perf.status_code, 200)
        self.assertEqual(len(res_perf.json()), 10)

        # Best sellers & Low performers
        res_top = self.client.get("/api/products/best-sellers", params={"limit": 5})
        self.assertEqual(res_top.status_code, 200)
        self.assertEqual(len(res_top.json()), 5)

        res_bot = self.client.get("/api/products/low-performers", params={"limit": 5})
        self.assertEqual(res_bot.status_code, 200)
        self.assertEqual(len(res_bot.json()), 5)

        # Customer segmentation: sums to total net revenue
        res_seg = self.client.get("/api/customers/segmentation")
        self.assertEqual(res_seg.status_code, 200)
        seg_data = res_seg.json()
        sum_seg_rev = sum(s["revenue"] for s in seg_data)
        self.assertAlmostEqual(sum_seg_rev, 25900147.21, places=2)

        # Top customers
        res_cust = self.client.get("/api/customers/top-customers", params={"limit": 10})
        self.assertEqual(res_cust.status_code, 200)
        self.assertEqual(len(res_cust.json()), 10)

    # -------------------------------------------------------------------------
    # Workflow H – Regional Analysis
    # -------------------------------------------------------------------------
    def test_workflow_h_regional_analysis(self):
        res_reg = self.client.get("/api/regional/performance")
        self.assertEqual(res_reg.status_code, 200)
        reg_data = res_reg.json()
        self.assertGreater(len(reg_data), 0)
        sum_reg_rev = sum(r["revenue"] for r in reg_data)
        self.assertAlmostEqual(sum_reg_rev, 25900147.21, places=2)

    # -------------------------------------------------------------------------
    # Workflow I – Reports and Exports
    # -------------------------------------------------------------------------
    def test_workflow_i_reports_and_exports(self):
        # Summary & Power BI models
        res_rep = self.client.get("/api/reports/summary")
        self.assertEqual(res_rep.status_code, 200)
        schemas.ExecutiveReport(**res_rep.json())

        res_pbi = self.client.get("/api/reports/power-bi/dataset")
        self.assertEqual(res_pbi.status_code, 200)
        pbi_data = res_pbi.json()
        self.assertIsInstance(pbi_data, list)
        self.assertGreater(len(pbi_data), 0)
        [schemas.PowerBiDatasetRow(**item) for item in pbi_data[:10]]

        # CSV streaming export
        res_csv = self.client.get("/api/reports/export/transactions/csv")
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.headers.get("content-type"), "text/csv; charset=utf-8")
        self.assertIn("attachment; filename=revenueguard_transactions.csv", res_csv.headers.get("content-disposition", ""))
        self.assertIn("order_id", res_csv.text)
        self.assertIn("gross_revenue", res_csv.text)
        self.assertIn("net_amount", res_csv.text)

        # Excel streaming export
        res_excel = self.client.get("/api/reports/export/transactions/excel")
        self.assertEqual(res_excel.status_code, 200)
        self.assertEqual(
            res_excel.headers.get("content-type"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.assertIn("attachment; filename=revenueguard_full_bi_report.xlsx", res_excel.headers.get("content-disposition", ""))
        self.assertGreater(len(res_excel.body), 100)

    # -------------------------------------------------------------------------
    # Workflow J – Data Management & Security Guard
    # -------------------------------------------------------------------------
    def test_workflow_j_data_management_security(self):
        # Safe SELECT execution
        res_sql = self.client.post("/api/data/execute-sql", json={"query": "SELECT COUNT(*) as cnt FROM orders;"})
        self.assertEqual(res_sql.status_code, 200)
        self.assertEqual(res_sql.json()["rows"][0]["cnt"], 5200)

        # Prohibited modifying statements rejected with 403 / 400
        prohibited = [
            "DROP TABLE orders",
            "UPDATE orders SET total_gross_amount = 0",
            "DELETE FROM orders WHERE id = 1",
            "ALTER TABLE orders ADD COLUMN hack TEXT",
            "SELECT 1; SELECT 2",
            "SELECT * FROM sqlite_master",
            "ATTACH DATABASE ':memory:' AS leak",
        ]
        for query in prohibited:
            res_block = self.client.post("/api/data/execute-sql", json={"query": query})
            self.assertIn(res_block.status_code, [400, 403], f"Query not blocked: {query}")

        # Ingestion validation
        valid_csv = (
            "order_number,order_date,customer_code,product_sku,quantity,unit_price,discount_amount\n"
            "ORD-WF-001,2026-06-01,CUST-00001,PRD-CLD-01,2,1499.0,100.0\n"
        ).encode("utf-8")
        res_val = self.client.post_file("/api/data/validate", filename="valid.csv", file_bytes=valid_csv)
        self.assertEqual(res_val.status_code, 200)
        val_data = res_val.json()
        self.assertEqual(val_data["valid_rows"], 1)
        self.assertEqual(val_data["invalid_rows"], 0)
        self.assertGreaterEqual(val_data["quality_score"], 90.0)

        # History audit log
        res_hist = self.client.get("/api/data/history")
        self.assertEqual(res_hist.status_code, 200)

    # -------------------------------------------------------------------------
    # Workflow K – Settings and Application Health
    # -------------------------------------------------------------------------
    def test_workflow_k_settings_and_health(self):
        res_health = self.client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        d_health = res_health.json()
        self.assertEqual(d_health["status"], "healthy")
        self.assertEqual(d_health["database"], "connected")
        self.assertIn("timestamp", d_health)


if __name__ == "__main__":
    unittest.main()
