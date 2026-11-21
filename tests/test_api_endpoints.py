import unittest
from backend.main import app
from tests.asgi_client import ASGITestClient
import backend.schemas as schemas


class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ASGITestClient(app)

    # ---------------------------------------------------------
    # 1. System & Health Endpoints
    # ---------------------------------------------------------
    def test_root_endpoint(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("platform", data)
        self.assertEqual(data["status"], "Operational")

    def test_health_check_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"], "connected")

    def test_openapi_schema(self):
        res = self.client.get("/openapi.json")
        self.assertEqual(res.status_code, 200)
        schema = res.json()
        self.assertIn("openapi", schema)
        self.assertIn("paths", schema)
        # Ensure all 45 endpoints are registered in OpenAPI schema
        self.assertEqual(len(schema["paths"]), 45)

    # ---------------------------------------------------------
    # 2. Overview Endpoints
    # ---------------------------------------------------------
    def test_overview_filters(self):
        res = self.client.get("/api/overview/filters")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.FilterOptions(**data)
        self.assertGreater(len(model.categories), 0)
        self.assertGreater(len(model.regions), 0)
        self.assertTrue(len(model.min_date) >= 10)
        self.assertTrue(len(model.max_date) >= 10)

    def test_overview_kpis(self):
        res = self.client.get("/api/overview/kpis")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.DashboardKPIs(**data)
        self.assertGreater(model.total_revenue.value, 0)
        self.assertGreater(model.total_orders.value, 0)

    def test_overview_trends(self):
        res = self.client.get("/api/overview/trends")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        items = [schemas.TrendDataPoint(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_overview_category_breakdown(self):
        res = self.client.get("/api/overview/category-breakdown")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.CategoryContribution(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_overview_top_products(self):
        res = self.client.get("/api/overview/top-products", params={"limit": 5})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 5)
        items = [schemas.ProductPerformanceItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_overview_regional_sales(self):
        res = self.client.get("/api/overview/regional-sales")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.RegionalPerformance(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_overview_recent_transactions(self):
        res = self.client.get("/api/overview/recent-transactions", params={"limit": 10})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 10)
        items = [schemas.RecentTransactionItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_overview_insights(self):
        res = self.client.get("/api/overview/insights")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.BusinessInsightItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    # ---------------------------------------------------------
    # 3. Revenue Endpoints
    # ---------------------------------------------------------
    def test_revenue_summary(self):
        res = self.client.get("/api/revenue/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.RevenueSummary(**data)
        self.assertGreater(model.gross_revenue.value, 0)

    def test_revenue_trends_monthly_and_quarterly(self):
        res_m = self.client.get("/api/revenue/trends", params={"grain": "monthly"})
        self.assertEqual(res_m.status_code, 200)
        data_m = res_m.json()
        self.assertIsInstance(data_m, list)
        self.assertGreater(len(data_m), 0)
        items_m = [schemas.TrendDataPoint(**item) for item in data_m]

        res_q = self.client.get("/api/revenue/trends", params={"grain": "quarterly"})
        self.assertEqual(res_q.status_code, 200)
        data_q = res_q.json()
        self.assertIsInstance(data_q, list)
        self.assertGreater(len(data_q), 0)
        self.assertLess(len(data_q), len(data_m))
        items_q = [schemas.TrendDataPoint(**item) for item in data_q]

    def test_revenue_by_category(self):
        res = self.client.get("/api/revenue/by-category")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.CategoryContribution(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_revenue_by_region(self):
        res = self.client.get("/api/revenue/by-region")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.RegionalPerformance(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_revenue_by_product(self):
        res = self.client.get("/api/revenue/by-product", params={"limit": 10})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.ProductPerformanceItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    # ---------------------------------------------------------
    # 4. Sales Endpoints
    # ---------------------------------------------------------
    def test_sales_summary(self):
        res = self.client.get("/api/sales/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.SalesSummary(**data)
        self.assertGreater(model.total_orders, 0)
        self.assertGreater(model.total_sales, 0)

    def test_sales_payment_methods(self):
        res = self.client.get("/api/sales/payment-methods")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        # Verify both legacy and frontend-compatible alias keys are present
        for row in data:
            model = schemas.PaymentMethodStats(**row)
            self.assertEqual(model.payment_method, model.name)
            self.assertEqual(model.orders_count, model.count)
            self.assertEqual(model.total_amount, model.revenue)
            self.assertEqual(model.total_amount, model.value)
            self.assertGreaterEqual(model.percentage, 0)

    def test_sales_transactions(self):
        res = self.client.get("/api/sales/transactions", params={"limit": 15, "offset": 0})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 15)
        items = [schemas.RecentTransactionItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    # ---------------------------------------------------------
    # 5. Discounts Endpoints
    # ---------------------------------------------------------
    def test_discounts_summary(self):
        res = self.client.get("/api/discounts/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.DiscountSummary(**data)
        self.assertGreater(model.total_discounts, 0)
        self.assertGreater(model.total_instances, 0)

    def test_discounts_by_type(self):
        res = self.client.get("/api/discounts/by-type")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.DiscountImpactItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_discounts_by_category(self):
        res = self.client.get("/api/discounts/by-category")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.CategoryDiscountImpact(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_discounts_high_discount_orders(self):
        res = self.client.get("/api/discounts/high-discount-orders", params={"threshold_pct": 20.0, "limit": 10})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 10)
        if len(data) > 0:
            self.assertIn("discount_amount", data[0])
            self.assertIn("discount_percentage", data[0])

    # ---------------------------------------------------------
    # 6. Refunds Endpoints
    # ---------------------------------------------------------
    def test_refunds_summary(self):
        res = self.client.get("/api/refunds/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.RefundSummary(**data)
        self.assertGreater(model.total_refund_amount, 0)
        self.assertGreater(model.total_refunds_count, 0)

    def test_refunds_reasons(self):
        res = self.client.get("/api/refunds/reasons")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.RefundReasonItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_refunds_by_category(self):
        res = self.client.get("/api/refunds/by-category")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.CategoryRefundImpact(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_refunds_high_refund_products(self):
        res = self.client.get("/api/refunds/high-refund-products", params={"limit": 10})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 10)
        items = [schemas.HighRefundProductItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    # ---------------------------------------------------------
    # 7. Profitability Endpoints
    # ---------------------------------------------------------
    def test_profitability_summary(self):
        res = self.client.get("/api/profitability/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.ProfitabilitySummary(**data)
        self.assertGreater(model.gross_revenue, 0)
        self.assertGreater(model.net_revenue, 0)
        self.assertGreater(model.gross_profit, 0)

    def test_profitability_monthly_trends(self):
        res = self.client.get("/api/profitability/monthly-trends")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.TrendDataPoint(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_profitability_product_quadrant(self):
        res = self.client.get("/api/profitability/product-quadrant")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.ProductQuadrantItem(**item) for item in data]
        self.assertGreater(len(items), 0)
        valid_quadrants = {
            "Star (High Revenue, High Margin)",
            "Workhorse (High Revenue, Low Margin)",
            "Niche Opportunity (Low Revenue, High Margin)",
            "Underperformer (Low Revenue, Low Margin)"
        }
        for item in items:
            self.assertIn(item.classification, valid_quadrants)

    # ---------------------------------------------------------
    # 8. Products Endpoints
    # ---------------------------------------------------------
    def test_products_performance(self):
        res = self.client.get("/api/products/performance", params={"limit": 20})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 20)
        items = [schemas.ProductPerformanceItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_products_best_sellers(self):
        res = self.client.get("/api/products/best-sellers", params={"limit": 5})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 5)
        items = [schemas.ProductPerformanceItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_products_low_performers(self):
        res = self.client.get("/api/products/low-performers", params={"limit": 5})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 5)
        items = [schemas.ProductPerformanceItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    # ---------------------------------------------------------
    # 9. Customers Endpoints
    # ---------------------------------------------------------
    def test_customers_summary(self):
        res = self.client.get("/api/customers/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.CustomerSummary(**data)
        self.assertGreater(model.total_customers, 0)

    def test_customers_segmentation(self):
        res = self.client.get("/api/customers/segmentation")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.CustomerSegmentStats(**item) for item in data]
        self.assertGreater(len(items), 0)

    def test_customers_top_customers(self):
        res = self.client.get("/api/customers/top-customers", params={"limit": 10})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 10)
        items = [schemas.TopCustomerItem(**item) for item in data]
        self.assertGreater(len(items), 0)

    # ---------------------------------------------------------
    # 10. Regional Endpoints
    # ---------------------------------------------------------
    def test_regional_performance(self):
        res = self.client.get("/api/regional/performance")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.RegionalPerformance(**item) for item in data]
        self.assertGreater(len(items), 0)

    # ---------------------------------------------------------
    # 11. Reports & Exports Endpoints
    # ---------------------------------------------------------
    def test_reports_summary(self):
        res = self.client.get("/api/reports/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        model = schemas.ExecutiveReport(**data)
        self.assertIn("total_revenue", model.kpis)
        self.assertGreater(len(model.categories), 0)
        self.assertGreater(len(model.regions), 0)

    def test_reports_export_csv(self):
        res = self.client.get("/api/reports/export/transactions/csv")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("content-type"), "text/csv; charset=utf-8")
        self.assertIn("order_number", res.text)
        self.assertIn("customer_name", res.text)

    def test_reports_export_excel(self):
        res = self.client.get("/api/reports/export/transactions/excel")
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", res.headers.get("content-type", ""))
        self.assertGreater(len(res.body), 100)

    def test_reports_power_bi_dataset(self):
        res = self.client.get("/api/reports/power-bi/dataset")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        items = [schemas.PowerBiDatasetRow(**item) for item in data[:20]]
        self.assertGreater(len(items), 0)

    # ---------------------------------------------------------
    # 12. Data Management Endpoints
    # ---------------------------------------------------------
    def test_data_history(self):
        res = self.client.get("/api/data/history")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        items = [schemas.UploadHistoryItem(**item) for item in data]

    def test_data_execute_sql_safe(self):
        # Test safe SELECT query
        payload = {"query": "SELECT COUNT(*) as total FROM orders;"}
        res = self.client.post("/api/data/execute-sql", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("rows", data)
        self.assertIn("columns", data)
        self.assertEqual(data["rows"][0]["total"], 5200)

    def test_data_execute_sql_blocked(self):
        # Non-SELECT statement should be rejected
        payload = {"query": "DROP TABLE orders;"}
        res = self.client.post("/api/data/execute-sql", json=payload)
        self.assertIn(res.status_code, [400, 403])

    def test_data_validate_empty_fails(self):
        # Missing file upload payload returns 422 Unprocessable Entity
        res = self.client.post("/api/data/validate")
        self.assertEqual(res.status_code, 422)

    # ---------------------------------------------------------
    # 13. Filter Parameter Integration Tests
    # ---------------------------------------------------------
    def test_date_and_category_filters(self):
        res_all = self.client.get("/api/overview/kpis")
        self.assertEqual(res_all.status_code, 200)
        total_rev_all = res_all.json()["total_revenue"]["value"]

        # Filter by specific date range
        res_filtered = self.client.get(
            "/api/overview/kpis",
            params={"start_date": "2024-01-01", "end_date": "2024-06-30"}
        )
        self.assertEqual(res_filtered.status_code, 200)
        total_rev_filtered = res_filtered.json()["total_revenue"]["value"]
        self.assertLess(total_rev_filtered, total_rev_all)

        # Filter by category_id
        res_cat = self.client.get(
            "/api/overview/kpis",
            params={"category_id": 1}
        )
        self.assertEqual(res_cat.status_code, 200)
        total_rev_cat = res_cat.json()["total_revenue"]["value"]
        self.assertLess(total_rev_cat, total_rev_all)


if __name__ == "__main__":
    unittest.main()
