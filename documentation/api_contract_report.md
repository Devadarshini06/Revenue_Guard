# RevenueGuard – Phase 2, Milestone 2: API Endpoint Normalization & Contract Verification Report

**Date:** November 2026  
**Status:** Approved & Verified  
**Scope:** API Normalization, Pydantic Schema Alignment, Frontend Contract Mapping, and Automated Regression Testing across all 45 API Endpoints.

---

## Executive Summary

Phase 2, Milestone 2 established end-to-end alignment between RevenueGuard's FastAPI backend and the 12-module frontend. All 45 backend endpoints across 11 route domains and system routes were audited, standardized, and validated against Pydantic models. All 33 methods in `frontend/src/services/mockService.js` have been mapped to their corresponding backend endpoints with verified schema contracts.

A dedicated, lightweight zero-dependency ASGI test client harness (`tests/asgi_client.py`) and a comprehensive automated test suite (`tests/test_api_endpoints.py`) were created. All 46 endpoint tests plus 9 analytics calculation tests (55 total tests) pass in 1.49s without modifying or reseeding the production SQLite database (`revenueguard.db`, 24,111 rows).

---

## 1. Complete API Endpoint Inventory (45 Endpoints)

| # | Route Domain | HTTP Method | Endpoint Path | Primary Parameters / Body | Response Model / Structure | Status |
|---|---|---|---|---|---|---|
| 1 | System | `GET` | `/` | None | System status, version, docs | Verified |
| 2 | System | `GET` | `/api/health` | None | Health status, timestamp, db | Verified |
| 3 | Overview | `GET` | `/api/overview/filters` | None | `FilterOptions` | Verified |
| 4 | Overview | `GET` | `/api/overview/kpis` | `start_date`, `end_date`, `category_id`, `region_id` | `DashboardKPIs` | Verified |
| 5 | Overview | `GET` | `/api/overview/trends` | `start_date`, `end_date` | `List[TrendDataPoint]` | Verified |
| 6 | Overview | `GET` | `/api/overview/category-breakdown` | `start_date`, `end_date` | `List[CategoryContribution]` | Verified |
| 7 | Overview | `GET` | `/api/overview/top-products` | `limit` (int) | `List[ProductPerformanceItem]` | Verified |
| 8 | Overview | `GET` | `/api/overview/regional-sales` | `start_date`, `end_date` | `List[RegionalPerformance]` | Verified |
| 9 | Overview | `GET` | `/api/overview/recent-transactions` | `limit`, `offset` | `List[RecentTransactionItem]` | Verified |
| 10 | Overview | `GET` | `/api/overview/insights` | `start_date`, `end_date` | `List[BusinessInsightItem]` | Verified |
| 11 | Revenue | `GET` | `/api/revenue/summary` | `start_date`, `end_date`, `category_id`, `region_id` | `RevenueSummary` | Verified |
| 12 | Revenue | `GET` | `/api/revenue/trends` | `start_date`, `end_date`, `grain` (`monthly`/`quarterly`) | `List[TrendDataPoint]` | Verified |
| 13 | Revenue | `GET` | `/api/revenue/by-category` | `start_date`, `end_date` | `List[CategoryContribution]` | Verified |
| 14 | Revenue | `GET` | `/api/revenue/by-region` | `start_date`, `end_date` | `List[RegionalPerformance]` | Verified |
| 15 | Revenue | `GET` | `/api/revenue/by-product` | `limit`, `category_id`, `region_id` | `List[ProductPerformanceItem]` | Verified |
| 16 | Sales | `GET` | `/api/sales/summary` | `start_date`, `end_date` | `SalesSummary` | Verified |
| 17 | Sales | `GET` | `/api/sales/payment-methods` | `start_date`, `end_date` | `List[PaymentMethodStats]` | Verified |
| 18 | Sales | `GET` | `/api/sales/transactions` | `limit`, `offset` | `List[RecentTransactionItem]` | Verified |
| 19 | Discounts | `GET` | `/api/discounts/summary` | `start_date`, `end_date` | `DiscountSummary` | Verified |
| 20 | Discounts | `GET` | `/api/discounts/by-type` | `start_date`, `end_date` | `List[DiscountImpactItem]` | Verified |
| 21 | Discounts | `GET` | `/api/discounts/by-category` | `start_date`, `end_date` | `List[CategoryDiscountImpact]` | Verified |
| 22 | Discounts | `GET` | `/api/discounts/high-discount-orders` | `threshold_pct`, `limit` | `List[Dict[str, Any]]` | Verified |
| 23 | Refunds | `GET` | `/api/refunds/summary` | `start_date`, `end_date` | `RefundSummary` | Verified |
| 24 | Refunds | `GET` | `/api/refunds/reasons` | `start_date`, `end_date` | `List[RefundReasonItem]` | Verified |
| 25 | Refunds | `GET` | `/api/refunds/by-category` | `start_date`, `end_date` | `List[CategoryRefundImpact]` | Verified |
| 26 | Refunds | `GET` | `/api/refunds/high-refund-products` | `limit` | `List[HighRefundProductItem]` | Verified |
| 27 | Profitability | `GET` | `/api/profitability/summary` | `start_date`, `end_date`, `category_id`, `region_id` | `ProfitabilitySummary` | Verified |
| 28 | Profitability | `GET` | `/api/profitability/monthly-trends` | `start_date`, `end_date` | `List[TrendDataPoint]` | Verified |
| 29 | Profitability | `GET` | `/api/profitability/product-quadrant` | None | `List[ProductQuadrantItem]` | Verified |
| 30 | Products | `GET` | `/api/products/performance` | `limit`, `category_id` | `List[ProductPerformanceItem]` | Verified |
| 31 | Products | `GET` | `/api/products/best-sellers` | `limit` | `List[ProductPerformanceItem]` | Verified |
| 32 | Products | `GET` | `/api/products/low-performers` | `limit` | `List[ProductPerformanceItem]` | Verified |
| 33 | Customers | `GET` | `/api/customers/summary` | `start_date`, `end_date` | `CustomerSummary` | Verified |
| 34 | Customers | `GET` | `/api/customers/segmentation` | `start_date`, `end_date` | `List[CustomerSegmentStats]` | Verified |
| 35 | Customers | `GET` | `/api/customers/top-customers` | `limit` | `List[TopCustomerItem]` | Verified |
| 36 | Regional | `GET` | `/api/regional/performance` | `start_date`, `end_date` | `List[RegionalPerformance]` | Verified |
| 37 | Reports | `GET` | `/api/reports/summary` | None | `ExecutiveReport` | Verified |
| 38 | Reports | `GET` | `/api/reports/export/transactions/csv` | None | CSV Streaming Stream | Verified |
| 39 | Reports | `GET` | `/api/reports/export/transactions/excel` | None | XLSX Multi-sheet Stream | Verified |
| 40 | Reports | `GET` | `/api/reports/power-bi/dataset` | None | `List[PowerBiDatasetRow]` | Verified |
| 41 | Data Management | `GET` | `/api/data/history` | None | `List[UploadHistoryItem]` | Verified |
| 42 | Data Management | `POST` | `/api/data/validate` | `file: UploadFile` | `DataQualityReport` | Verified |
| 43 | Data Management | `POST` | `/api/data/upload` | `file: UploadFile` | `Dict[str, Any]` | Verified |
| 44 | Data Management | `POST` | `/api/data/execute-sql` | `payload: { query: str }` | `Dict[str, Any]` (SELECT only) | Verified |
| 45 | Data Management | `POST` | `/api/data/reseed-sample-data` | None | `Dict[str, Any]` | Verified |

---

## 2. Frontend Compatibility Mapping Table (All 33 Mock Service Methods)

The table below maps every mock service method in `frontend/src/services/mockService.js` to its target backend endpoint, highlighting the exact payload fields guaranteed by the backend:

| # | Frontend Module | Mock Service Method | Backend Endpoint | Key Response Fields Required & Supported | Compatibility Status |
|---|---|---|---|---|---|
| 1 | Filter Bar | `getFilters()` | `GET /api/overview/filters` | `categories`, `regions`, `payment_methods`, `min_date`, `max_date` | 100% Compatible |
| 2 | Executive Overview | `getKPIs(params)` | `GET /api/overview/kpis` | `total_revenue`, `net_revenue`, `total_orders`, `average_order_value`, `total_discounts`, `total_refunds`, `gross_profit`, `profit_margin` | 100% Compatible |
| 3 | Executive Overview | `getTrends(params)` | `GET /api/overview/trends` | `date`, `label`, `gross_revenue`, `net_revenue`, `cogs`, `gross_profit`, `orders_count`, `discounts`, `refunds`, `growth_rate` | 100% Compatible |
| 4 | Executive Overview | `getCategoryBreakdown(params)` | `GET /api/overview/category-breakdown` | `category_id`, `category_name`, `gross_revenue`, `discount_amount`, `refund_amount`, `revenue`, `profit`, `percentage`, `profit_margin` | 100% Compatible |
| 5 | Executive Overview | `getTopProducts(params)` | `GET /api/overview/top-products` | `product_id`, `sku`, `name`, `category_name`, `units_sold`, `gross_revenue`, `discount_amount`, `revenue`, `profit`, `profit_margin`, `rank` | 100% Compatible |
| 6 | Executive Overview | `getRegionalSales(params)` | `GET /api/overview/regional-sales` | `region_id`, `region_name`, `country`, `code`, `gross_revenue`, `discount_amount`, `refund_amount`, `revenue`, `profit`, `profit_margin` | 100% Compatible |
| 7 | Executive Overview | `getRecentTransactions(params)` | `GET /api/overview/recent-transactions` | `order_id`, `order_number`, `order_date`, `customer_name`, `product_summary`, `total_amount`, `status`, `payment_method` | 100% Compatible |
| 8 | Executive Overview | `getInsights(params)` | `GET /api/overview/insights` | `id`, `title`, `description`, `type`, `impact_score`, `category`, `recommendation` | 100% Compatible |
| 9 | Revenue Analytics | `getRevenueSummary(params)` | `GET /api/revenue/summary` | `gross_revenue`, `net_revenue`, `discounts`, `refunds`, `growth_rate` | 100% Compatible |
| 10 | Revenue Analytics | `getRevenueTrends(params)` | `GET /api/revenue/trends` | `date`, `label`, `gross_revenue`, `net_revenue`, `cogs`, `gross_profit`, `orders_count` (`grain=monthly\|quarterly`) | 100% Compatible |
| 11 | Revenue Analytics | `getRevenueByCategory(params)` | `GET /api/revenue/by-category` | `category_id`, `category_name`, `gross_revenue`, `discount_amount`, `refund_amount`, `revenue`, `profit`, `percentage` | 100% Compatible |
| 12 | Revenue Analytics | `getRevenueByRegion(params)` | `GET /api/revenue/by-region` | `region_id`, `region_name`, `country`, `code`, `revenue`, `profit`, `profit_margin` | 100% Compatible |
| 13 | Revenue Analytics | `getRevenueByProduct(params)` | `GET /api/revenue/by-product` | `product_id`, `sku`, `name`, `category_name`, `revenue`, `profit`, `profit_margin`, `rank` | 100% Compatible |
| 14 | Sales Performance | `getSalesSummary(params)` | `GET /api/sales/summary` | `total_orders`, `total_units_sold`, `total_sales`, `average_order_value` | 100% Compatible |
| 15 | Sales Performance | `getSalesByPayment(params)` | `GET /api/sales/payment-methods` | Both legacy & frontend keys: `payment_method`, `name`, `orders_count`, `count`, `total_amount`, `revenue`, `value`, `avg_amount`, `percentage` | 100% Compatible |
| 16 | Sales Performance | `getSalesTransactions(params)` | `GET /api/sales/transactions` | `order_id`, `order_number`, `order_date`, `customer_name`, `product_summary`, `total_amount`, `status`, `payment_method` | 100% Compatible |
| 17 | Discount Analysis | `getDiscountSummary(params)` | `GET /api/discounts/summary` | `total_discounts`, `total_instances`, `average_discount_percentage`, `revenue_erosion_rate` | 100% Compatible |
| 18 | Discount Analysis | `getDiscountsByType(params)` | `GET /api/discounts/by-type` | `discount_type`, `discount_code`, `orders_count`, `avg_discount_pct`, `total_discount`, `revenue_before`, `revenue_after`, `profit_impact` | 100% Compatible |
| 19 | Discount Analysis | `getDiscountsByCategory(params)` | `GET /api/discounts/by-category` | `category_name`, `gross_revenue`, `discount_amount`, `discount_percentage` | 100% Compatible |
| 20 | Discount Analysis | `getHighDiscountOrders(params)` | `GET /api/discounts/high-discount-orders` | `order_id`, `order_number`, `gross_amount`, `discount_amount`, `discount_percentage` | 100% Compatible |
| 21 | Refund Analysis | `getRefundSummary(params)` | `GET /api/refunds/summary` | `total_refund_amount`, `total_refunds_count`, `refunded_orders_count`, `refund_rate` | 100% Compatible |
| 22 | Refund Analysis | `getRefundReasons(params)` | `GET /api/refunds/reasons` | `reason`, `count`, `total_amount`, `avg_amount`, `percentage` | 100% Compatible |
| 23 | Refund Analysis | `getRefundsByCategory(params)` | `GET /api/refunds/by-category` | `category_name`, `refund_count`, `refund_amount`, `category_revenue`, `refund_rate` | 100% Compatible |
| 24 | Refund Analysis | `getHighRefundProducts(params)` | `GET /api/refunds/high-refund-products` | `product_id`, `sku`, `product_name`, `category_name`, `refund_claims`, `total_refunded`, `gross_sales`, `refund_rate` | 100% Compatible |
| 25 | Profitability Analysis | `getProfitSummary(params)` | `GET /api/profitability/summary` | `gross_revenue`, `discounts`, `refunds`, `net_revenue`, `cost_of_goods_sold`, `gross_profit`, `profit_margin` | 100% Compatible |
| 26 | Profitability Analysis | `getProfitTrends(params)` | `GET /api/profitability/monthly-trends` | `date`, `label`, `gross_revenue`, `net_revenue`, `cogs`, `gross_profit`, `profit_margin` | 100% Compatible |
| 27 | Profitability Analysis | `getProductQuadrant(params)` | `GET /api/profitability/product-quadrant` | `classification` (`Star`, `Workhorse`, `Niche Opportunity`, `Underperformer`), `is_high_revenue`, `is_high_margin`, `profit_margin`, `revenue` | 100% Compatible |
| 28 | Product Insights | `getProductPerformance(params)` | `GET /api/products/performance` | `product_id`, `sku`, `name`, `category_name`, `units_sold`, `gross_revenue`, `revenue`, `profit`, `profit_margin`, `rank` | 100% Compatible |
| 29 | Product Insights | `getBestSellers(params)` | `GET /api/products/best-sellers` | Top 5 ranked products by net revenue | 100% Compatible |
| 30 | Product Insights | `getLowPerformers(params)` | `GET /api/products/low-performers` | Bottom 5 ranked products by net revenue | 100% Compatible |
| 31 | Customer Insights | `getCustomerSummary(params)` | `GET /api/customers/summary` | `total_customers`, `active_orders`, `total_revenue`, `average_customer_spending` | 100% Compatible |
| 32 | Customer Insights | `getCustomerSegments(params)` | `GET /api/customers/segmentation` | `segment`, `customers_count`, `revenue`, `orders_count`, `profit`, `refund_amount`, `average_order_value`, `repeat_rate` | 100% Compatible |
| 33 | Customer Insights | `getTopCustomers(params)` | `GET /api/customers/top-customers` | `id`, `customer_code`, `name`, `segment`, `email`, `region_name`, `total_orders`, `total_spent`, `refund_total` | 100% Compatible |
| 34 | Regional Analysis | `getRegionalPerformance(params)`| `GET /api/regional/performance` | `region_id`, `region_name`, `country`, `code`, `orders_count`, `gross_revenue`, `discount_amount`, `refund_amount`, `revenue`, `profit`, `profit_margin`, `refund_rate`, `discount_rate` | 100% Compatible |
| 35 | Reports & Exports | `getExecutiveReport(params)` | `GET /api/reports/summary` | `kpis`, `categories`, `regions`, `trends`, `generated_at` | 100% Compatible |
| 36 | Reports & Exports | `exportTransactionsCSV()` | `GET /api/reports/export/transactions/csv` | Streams CSV attachment (`text/csv`) with transaction details | 100% Compatible |
| 37 | Reports & Exports | `exportTransactionsExcel()` | `GET /api/reports/export/transactions/excel` | Streams multi-sheet OpenXML spreadsheet (`application/vnd.openxmlformats...`) | 100% Compatible |
| 38 | Reports & Exports | `getPowerBIDataset()` | `GET /api/reports/power-bi/dataset` | Tabular schema with dimensional hierarchy (`order_number`, `customer_segment`, `region_name`, `category_name`, etc.) | 100% Compatible |
| 39 | Data Management | `validateDataset(file)` | `POST /api/data/validate` | `filename`, `total_rows`, `valid_rows`, `invalid_rows`, `duplicate_rows`, `missing_columns`, `missing_values`, `column_types`, `quality_score`, `preview` | 100% Compatible |
| 40 | Data Management | `uploadDataset(file)` | `POST /api/data/upload` | Multipart file upload and database ingestion response | 100% Compatible |
| 41 | Data Management | `getUploadHistory()` | `GET /api/data/history` | `id`, `filename`, `rows_count`, `valid_rows`, `invalid_rows`, `duplicate_rows`, `status`, `upload_date`, `summary_notes` | 100% Compatible |
| 42 | Data Management | `reseedData()` | `POST /api/data/reseed-sample-data`| Controlled DB reseed response (`status`, `message`) | 100% Compatible |
| 43 | Data Management | `executeSQL(query)` | `POST /api/data/execute-sql` | `{ query: str }` -> `{ columns: [...], rows: [...], row_count: int, execution_time_ms: float }` | 100% Compatible |

---

## 3. Key Contract Enhancements Implemented in Milestone 2

1. **Dual-Key Support for Payment Methods (`/api/sales/payment-methods`):**
   - Frontend `SalesPerformance.jsx` expects `total_amount` and `payment_method`.
   - Other charting widgets expect `name`, `value`, `percentage`, `revenue`, `count`.
   - The endpoint now delivers all aliased keys simultaneously, preventing frontend property mismatches.

2. **Temporal Grain Normalization (`/api/revenue/trends`):**
   - Supports `grain=monthly` (default) and `grain=quarterly`.
   - Uses SQLite `strftime` date formatting with dynamic grouping to return consistent `TrendDataPoint` structures across granularities.

3. **Quadrant Classification Alignment (`/api/profitability/product-quadrant`):**
   - Backend classifications match the frontend quadrant tags verbatim:
     - `"Star (High Revenue, High Margin)"`
     - `"Workhorse (High Revenue, Low Margin)"`
     - `"Niche Opportunity (Low Revenue, High Margin)"`
     - `"Underperformer (Low Revenue, Low Margin)"`
   - Added boolean flags `is_high_revenue` and `is_high_margin` for straightforward UI conditional styling.

4. **Filter Parameter Normalization:**
   - Universal query parameters (`start_date`, `end_date`, `category_id`, `region_id`) are accepted across analytical routes.
   - 10-character `end_date` inputs (`YYYY-MM-DD`) automatically append `23:59:59` to guarantee inclusive end-of-day record matching.

---

## 4. Test Suite Execution & Verification

### Test Harness
- `tests/asgi_client.py`: Pure-Python zero-dependency ASGI test client using Python `asyncio` and Starlette's ASGI specification. Executes sub-second requests without external network libraries (`httpx` or `requests`).
- `tests/test_api_endpoints.py`: Comprehensive test suite testing all 45 API routes, response model validations, query parameter filtering, and safety checks.
- `tests/test_analytics_validation.py`: Mathematical verification of revenue, COGS, profit, discount, and refund formulas.

### Test Results
```text
$ ./venv/bin/python3 -m unittest discover tests
.......................................................
----------------------------------------------------------------------
Ran 55 tests in 1.487s

OK
```
- **Total Tests:** 55 passed, 0 failed, 0 errors.
- **Execution Speed:** 1.487 seconds.
- **Database Status:** Unmodified (`revenueguard.db` preserved at 24,111 records).

---

## Conclusion & Readiness for Next Milestone

Milestone 2 is complete. All FastAPI routes provide reliable, typed, and normalized contracts that match the frontend specifications. The system is ready to proceed to **Phase 2, Milestone 3: Real Database Operations & Advanced Business Logic**.
