import unittest
from backend.main import app
from tests.asgi_client import ASGITestClient
import backend.schemas as schemas


class TestFrontendBackendIntegration(unittest.TestCase):
    """
    End-to-End Integration Test Suite validating frontend-to-backend API contract bindings.
    Ensures that every frontend service method in frontend/src/services/api.js receives
    the expected data structure, correct financial baselines, and clean error states.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = ASGITestClient(app)

    # -------------------------------------------------------------------------
    # 1. Baseline Reporting Period Verification (Trailing 12M vs All-Time)
    # -------------------------------------------------------------------------
    def test_frontend_default_kpis_match_trailing_12m(self):
        """Verifies that the default KPI endpoint returns the Trailing 12-Month baseline for the UI."""
        res = self.client.get("/api/overview/kpis")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.DashboardKPIs(**data)

        # Asserts default trailing 12-month baseline
        self.assertEqual(int(model.total_orders.value), 3822)
        self.assertAlmostEqual(model.total_revenue.value, 28488467.00, places=2)
        self.assertAlmostEqual(model.net_revenue.value, 25900147.21, places=2)
        self.assertAlmostEqual(model.gross_profit.value, 10210727.21, places=2)
        self.assertAlmostEqual(model.total_discounts.value, 1670808.06, places=2)
        self.assertAlmostEqual(model.total_refunds.value, 917511.73, places=2)
        self.assertAlmostEqual(model.profit_margin.value, 39.42, places=1)
        self.assertAlmostEqual(model.average_order_value.value, 6776.60, places=1)

    def test_frontend_all_time_kpis_match_all_time_baseline(self):
        """Verifies that when 'All Time Data' is selected in the UI, the 18-month baseline is returned."""
        res = self.client.get("/api/overview/kpis", params={"start_date": "2020-01-01", "end_date": "2030-01-01"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.DashboardKPIs(**data)

        # Asserts all-time baseline (5,200 orders)
        self.assertEqual(int(model.total_orders.value), 5200)
        self.assertAlmostEqual(model.total_revenue.value, 38625502.00, places=2)
        self.assertAlmostEqual(model.net_revenue.value, 35021057.61, places=2)
        self.assertAlmostEqual(model.gross_profit.value, 13882547.61, places=2)
        self.assertAlmostEqual(model.total_discounts.value, 2342815.06, places=2)
        self.assertAlmostEqual(model.total_refunds.value, 1261629.33, places=2)
        self.assertAlmostEqual(model.profit_margin.value, 39.64, places=1)
        self.assertAlmostEqual(model.average_order_value.value, 6734.82, places=1)

    # -------------------------------------------------------------------------
    # 2. UI Widget Data Contracts
    # -------------------------------------------------------------------------
    def test_sales_payment_methods_has_both_legacy_and_chart_keys(self):
        """SalesPerformance page and Recharts pie chart require both naming sets."""
        res = self.client.get("/api/sales/payment-methods")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(len(data), 0)

        for item in data:
            self.assertIn("payment_method", item)
            self.assertIn("name", item)
            self.assertIn("total_amount", item)
            self.assertIn("revenue", item)
            self.assertIn("value", item)
            self.assertIn("percentage", item)
            self.assertIn("orders_count", item)
            self.assertIn("count", item)

    def test_profitability_product_quadrant_classifications(self):
        """ProfitabilityAnalysis page quadrant scatter chart checks specific classification tags."""
        res = self.client.get("/api/profitability/product-quadrant")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(len(data), 0)

        quadrant_set = {
            "Star (High Revenue, High Margin)",
            "Workhorse (High Revenue, Low Margin)",
            "Niche Opportunity (Low Revenue, High Margin)",
            "Underperformer (Low Revenue, Low Margin)"
        }
        for item in data:
            self.assertIn(item["classification"], quadrant_set)
            self.assertIn("is_high_revenue", item)
            self.assertIn("is_high_margin", item)

    def test_customer_segmentation_contract(self):
        """CustomerInsights page requires segment stats with AOV and repeat rate."""
        res = self.client.get("/api/customers/segmentation")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 4) # Enterprise, Mid-Market, SMB, Direct Consumer

        for seg in data:
            self.assertIn("segment", seg)
            self.assertIn("revenue", seg)
            self.assertIn("orders_count", seg)
            self.assertIn("average_order_value", seg)

    def test_reports_summary_matches_executive_report_model(self):
        """Reports & Exports board-ready summary structure."""
        res = self.client.get("/api/reports/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.ExecutiveReport(**data)
        self.assertIn("total_revenue", model.kpis)
        self.assertGreater(len(model.categories), 0)
        self.assertGreater(len(model.regions), 0)
        self.assertGreater(len(model.trends), 0)

    # -------------------------------------------------------------------------
    # 3. CSV and Excel Native Export Endpoints
    # -------------------------------------------------------------------------
    def test_export_transactions_csv_headers(self):
        res = self.client.get("/api/reports/export/transactions/csv")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("content-type"), "text/csv; charset=utf-8")
        self.assertIn("attachment; filename=revenueguard_transactions.csv", res.headers.get("content-disposition", ""))
        self.assertIn("order_number", res.text)
        self.assertIn("customer_name", res.text)
        self.assertIn("gross_revenue", res.text)
        self.assertIn("net_amount", res.text)

    def test_export_transactions_excel_headers(self):
        res = self.client.get("/api/reports/export/transactions/excel")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.headers.get("content-type"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.assertIn("attachment; filename=revenueguard_full_bi_report.xlsx", res.headers.get("content-disposition", ""))
        self.assertGreater(len(res.body), 100)

    # -------------------------------------------------------------------------
    # 4. Filter Parameter Integration
    # -------------------------------------------------------------------------
    def test_category_and_region_filters_flow_correctly(self):
        """Verifies that passing category_id and region_id filters data consistently."""
        res_cat = self.client.get("/api/overview/kpis", params={"category_id": 1})
        self.assertEqual(res_cat.status_code, 200)
        data_cat = res_cat.json()
        self.assertGreater(data_cat["total_orders"]["value"], 0)
        self.assertLess(data_cat["total_revenue"]["value"], 28488467.00)

        res_reg = self.client.get("/api/overview/kpis", params={"region_id": 1})
        self.assertEqual(res_reg.status_code, 200)
        data_reg = res_reg.json()
        self.assertGreater(data_reg["total_orders"]["value"], 0)
        self.assertLess(data_reg["total_revenue"]["value"], 28488467.00)


if __name__ == "__main__":
    unittest.main()
