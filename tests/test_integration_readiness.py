import unittest
from backend.main import app
from tests.asgi_client import ASGITestClient
import backend.schemas as schemas


class TestIntegrationReadiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ASGITestClient(app)

    # -------------------------------------------------------------------------
    # 1. Edge-Case Date Filters & Empty Datasets
    # -------------------------------------------------------------------------
    def test_future_date_range_returns_zero_kpis_cleanly(self):
        """When querying a date range with no transactions, KPIs should return zeros without failing."""
        res = self.client.get(
            "/api/overview/kpis",
            params={"start_date": "2099-01-01", "end_date": "2099-12-31"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.DashboardKPIs(**data)
        self.assertEqual(model.total_revenue.value, 0.0)
        self.assertEqual(model.total_orders.value, 0)
        self.assertEqual(model.net_revenue.value, 0.0)
        self.assertEqual(model.average_order_value.value, 0.0)

    def test_future_date_range_returns_empty_trends_cleanly(self):
        res = self.client.get(
            "/api/revenue/trends",
            params={"start_date": "2099-01-01", "end_date": "2099-12-31"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_inverted_date_range_handled_cleanly(self):
        """start_date after end_date should yield zero results rather than a 500 error."""
        res = self.client.get(
            "/api/overview/kpis",
            params={"start_date": "2026-12-31", "end_date": "2025-01-01"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_orders"]["value"], 0)

    def test_nonexistent_category_and_region_filters(self):
        res = self.client.get(
            "/api/overview/kpis",
            params={"category_id": 999999, "region_id": 999999}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_orders"]["value"], 0)
        self.assertEqual(data["total_revenue"]["value"], 0.0)

    # -------------------------------------------------------------------------
    # 2. Strict Input Validation & Error Responses
    # -------------------------------------------------------------------------
    def test_malformed_query_parameter_returns_422(self):
        """Non-numeric category_id returns standard 422 Unprocessable Entity."""
        res = self.client.get("/api/overview/kpis", params={"category_id": "not-an-integer"})
        self.assertEqual(res.status_code, 422)
        data = res.json()
        self.assertIn("detail", data)

    def test_empty_sql_query_returns_400(self):
        res = self.client.post("/api/data/execute-sql", json={"query": ""})
        self.assertEqual(res.status_code, 400)
        self.assertIn("SQL query cannot be empty", res.json()["detail"])

    def test_empty_file_upload_validation(self):
        res = self.client.post_file(
            "/api/data/validate",
            filename="empty_file.csv",
            file_bytes=b"",
            content_type="text/csv"
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Failed to parse file", res.json()["detail"])

    def test_malformed_csv_file_validation(self):
        # A file with conflicting inconsistent lines
        res = self.client.post_file(
            "/api/data/validate",
            filename="malformed.csv",
            file_bytes=b"header1,header2\nval1,val2,val3,val4\n",
            content_type="text/csv"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        # Should detect missing required schema columns cleanly without crashing
        self.assertEqual(data["valid_rows"], 0)
        self.assertGreater(len(data["missing_columns"]), 0)

    # -------------------------------------------------------------------------
    # 3. Real Database Financial Reconciliation Assertions
    # -------------------------------------------------------------------------
    def test_category_sums_match_kpis_exactly(self):
        """Cross-checks category breakdown sums against executive KPI totals."""
        res_kpis = self.client.get("/api/overview/kpis")
        self.assertEqual(res_kpis.status_code, 200)
        kpis = res_kpis.json()
        kpi_gross = kpis["total_revenue"]["value"]
        kpi_net = kpis["net_revenue"]["value"]
        kpi_disc = kpis["total_discounts"]["value"]
        kpi_ref = kpis["total_refunds"]["value"]
        kpi_profit = kpis["gross_profit"]["value"]

        res_cats = self.client.get("/api/overview/category-breakdown")
        self.assertEqual(res_cats.status_code, 200)
        cats = res_cats.json()
        self.assertGreater(len(cats), 0)

        sum_cat_gross = round(sum(c["gross_revenue"] for c in cats), 2)
        sum_cat_net = round(sum(c["revenue"] for c in cats), 2)
        sum_cat_disc = round(sum(c["discount_amount"] for c in cats), 2)
        sum_cat_ref = round(sum(c["refund_amount"] for c in cats), 2)
        sum_cat_profit = round(sum(c["profit"] for c in cats), 2)

        self.assertAlmostEqual(sum_cat_gross, kpi_gross, places=2)
        self.assertAlmostEqual(sum_cat_net, kpi_net, places=2)
        self.assertAlmostEqual(sum_cat_disc, kpi_disc, places=2)
        self.assertAlmostEqual(sum_cat_ref, kpi_ref, places=2)
        self.assertAlmostEqual(sum_cat_profit, kpi_profit, places=2)

    def test_regional_sums_match_kpis_exactly(self):
        """Cross-checks regional breakdown sums against executive KPI totals."""
        res_kpis = self.client.get("/api/overview/kpis")
        self.assertEqual(res_kpis.status_code, 200)
        kpis = res_kpis.json()
        kpi_gross = kpis["total_revenue"]["value"]
        kpi_net = kpis["net_revenue"]["value"]
        kpi_profit = kpis["gross_profit"]["value"]

        res_regs = self.client.get("/api/overview/regional-sales")
        self.assertEqual(res_regs.status_code, 200)
        regs = res_regs.json()
        self.assertGreater(len(regs), 0)

        sum_reg_gross = round(sum(r["gross_revenue"] for r in regs), 2)
        sum_reg_net = round(sum(r["revenue"] for r in regs), 2)
        sum_reg_profit = round(sum(r["profit"] for r in regs), 2)

        self.assertAlmostEqual(sum_reg_gross, kpi_gross, places=2)
        self.assertAlmostEqual(sum_reg_net, kpi_net, places=2)
        self.assertAlmostEqual(sum_reg_profit, kpi_profit, places=2)

    # -------------------------------------------------------------------------
    # 4. Engine-Level Authorizer Protection Tests
    # -------------------------------------------------------------------------
    def test_authorizer_denies_hidden_mutation_in_cte(self):
        """Verifies that attempt to delete within a CTE is denied."""
        payload = {"query": "WITH sneaky AS (DELETE FROM orders RETURNING *) SELECT * FROM sneaky;"}
        res = self.client.post("/api/data/execute-sql", json=payload)
        self.assertEqual(res.status_code, 403)

    def test_authorizer_denies_sqlite_temp_master(self):
        payload = {"query": "SELECT * FROM sqlite_temp_master;"}
        res = self.client.post("/api/data/execute-sql", json=payload)
        self.assertEqual(res.status_code, 403)

    # -------------------------------------------------------------------------
    # 5. Health & System Verification
    # -------------------------------------------------------------------------
    def test_health_check_returns_database_connected(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"], "connected")
        self.assertIn("timestamp", data)


if __name__ == "__main__":
    unittest.main()

