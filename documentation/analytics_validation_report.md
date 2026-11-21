# RevenueGuard – Phase 2, Milestone 1: Analytics Validation & Query Refactoring Report

## Executive Summary

This report documents the completion of **Milestone 1: Analytical Query Correction & Analytics Engine Refactoring**.

The objective of this milestone was to correct critical SQL join fan-out aggregation errors, standardize enterprise financial formulas, eliminate date-boundary leakage, and mathematically reconcile all analytics calculations against ground-truth database records.

- **Status**: **100% VERIFIED & PASSED**
- **Automated Test Suite**: 9 comprehensive test cases in `tests/test_analytics_validation.py` (**9 passed, 0 failures, 0.114s execution time**)
- **Database Preserved**: Intact (`revenueguard.db` with 24,111 total rows across 10 tables)
- **Frontend Preserved**: Frozen and isolated; no frontend code modified

---

## 1. Original Calculation Problems Identified

### Problem A: Cartesian Fan-Out on Refunds in `KPI_SUMMARY_QUERY`
In the original `KPI_SUMMARY_QUERY`:
```sql
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN refunds r ON o.id = r.order_id
```
- **The Defect**: Joining `order_items` (1-to-many from `orders`) directly with `refunds` (1-to-many from `orders`) caused SQLite to compute an unaggregated Cartesian product.
- **The Empirical Impact**:
  - The database contains 410 refunded orders with an average of 1.795 line items per order.
  - Every refund amount was duplicated for each line item on that order, generating 736 joined rows instead of 410.
  - Total refunds were reported as **$2,404,164.54** instead of the true **$1,261,629.33** (**1.91x artificial inflation**).
  - Consequently, Net Realized Revenue was deflated by **$1,142,535.21**, Gross Profit was deflated by **$1,142,535.21**, Profit Margin was distorted by **-2.04%**, and AOV was depressed by **-$219.72**.

### Problem B: Date Filtering Leakage in `PRODUCT_PERFORMANCE_QUERY`
In the original query:
```sql
FROM products p
JOIN categories c ON p.category_id = c.id
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.id AND o.order_date >= :start_date AND o.order_date <= :end_date
```
- **The Defect**: Because `orders` was a `LEFT JOIN` on `oi`, when `o.order_date` fell outside the filtered range, `o.id` was set to NULL, but `oi` was still present in the row set.
- **The Empirical Impact**: When querying an out-of-range date (e.g. `2020-01-01`), the query still returned all 855 units and $5.13M of revenue because `oi` records were never filtered out.

### Problem C: Date Boundary Truncation on End Dates
- **The Defect**: When the frontend sent ISO date strings without timestamps (e.g. `2026-11-14`), Python parsed them as `2026-11-14 00:00:00`.
- **The Empirical Impact**: Orders placed later in the day on the end date (e.g. at `02:36:14`) were unintentionally dropped from analytical windows.

### Problem D: Missing Regional Filter on Monthly Refunds
- **The Defect**: In `MONTHLY_REVENUE_TREND_QUERY`, `monthly_refunds` did not filter by `region_id`, deducting global company refunds from regional revenue figures.

---

## 2. Corrected SQL Architecture

All queries have been refactored in `backend/analytics/sql_queries.py` using isolated Common Table Expressions (CTEs):

### 1. Isolated Pre-Aggregation Architecture (`KPI_SUMMARY_QUERY`)
Order items and refunds are aggregated into distinct CTEs grouped by `order_id` before joining to `orders`:

```sql
WITH cur_items AS (
    SELECT
        oi.order_id,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.discount_amount), 0.0) AS total_discounts,
        COALESCE(SUM(oi.net_revenue), 0.0) AS net_revenue,
        COALESCE(SUM(oi.cogs), 0.0) AS total_cogs
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    WHERE (:category_id IS NULL OR p.category_id = :category_id)
    GROUP BY oi.order_id
),
cur_refunds AS (
    SELECT
        r.order_id,
        COALESCE(SUM(r.refund_amount), 0.0) AS total_refunds
    FROM refunds r
    JOIN order_items oi ON r.order_item_id = oi.id
    JOIN products p ON oi.product_id = p.id
    WHERE (:category_id IS NULL OR p.category_id = :category_id)
    GROUP BY r.order_id
),
current_period AS (
    SELECT
        COUNT(DISTINCT o.id) AS total_orders,
        COALESCE(SUM(ci.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(ci.total_discounts), 0.0) AS total_discounts,
        COALESCE(SUM(cr.total_refunds), 0.0) AS total_refunds,
        (COALESCE(SUM(ci.net_revenue), 0.0) - COALESCE(SUM(cr.total_refunds), 0.0)) AS net_revenue,
        COALESCE(SUM(ci.total_cogs), 0.0) AS total_cogs,
        (COALESCE(SUM(ci.net_revenue), 0.0) - COALESCE(SUM(cr.total_refunds), 0.0) - COALESCE(SUM(ci.total_cogs), 0.0)) AS gross_profit
    FROM orders o
    JOIN cur_items ci ON o.id = ci.order_id
    LEFT JOIN cur_refunds cr ON o.id = cr.order_id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date
      AND (:region_id IS NULL OR o.region_id = :region_id)
)
```

### 2. Inner-Scoped Date Joins (`PRODUCT_PERFORMANCE_QUERY`)
Enclosed the order item and order join inside an inner scope to prevent phantom row generation:
```sql
FROM products p
JOIN categories c ON p.category_id = c.id
LEFT JOIN (
    order_items oi 
    JOIN orders o ON oi.order_id = o.id AND o.order_date >= :start_date AND o.order_date <= :end_date
) ON p.id = oi.product_id
LEFT JOIN refunds r ON oi.id = r.order_item_id
```

### 3. End-of-Day Precision Normalization (`get_date_bounds`)
Updated date resolution in `backend/analytics/engine.py` to automatically normalize date strings:
```python
if len(clean_end) == 10:
    end_dt = datetime.fromisoformat(clean_end).replace(hour=23, minute=59, second=59)
```

---

## 3. Standardized Financial Formulas

| Metric | Standardized Formula | Definition & Constraints |
|---|---|---|
| **Gross Revenue** | $\sum (\text{quantity} \times \text{unit\_price})$ | Total contract/list price value before promotional concessions or returns. |
| **Promotional Discounts** | $\sum \text{discount\_amount}$ | Total price concessions applied at order-item level. Deducted exactly once. |
| **Refund Leakage** | $\sum \text{refund\_amount}$ | Total refunded capital from approved RMAs. Linked directly to order line item. |
| **Net Realized Revenue** | $\text{Gross Revenue} - \text{Discounts} - \text{Refunds}$ | Realized monetary inflow. Equals $\sum \text{orders.total\_net\_amount}$. |
| **Cost of Goods Sold (COGS)**| $\sum (\text{quantity} \times \text{unit\_cost})$ | Direct procurement, infrastructure, and delivery costs. |
| **Gross Profit** | $\text{Net Realized Revenue} - \text{COGS}$ | Residual earnings after commercial deductions and direct costs. |
| **Gross Profit Margin** | $(\text{Gross Profit} / \text{Net Realized Revenue}) \times 100$ | Margin yield on net recognized revenue. Safe against 0 denominator. |
| **Average Order Value (AOV)** | $\text{Net Realized Revenue} / \text{Total Unique Orders}$ | Net sales generated per unique commercial order. Safe against 0 orders. |
| **Revenue Growth Rate** | $[(\text{Net}_{t} - \text{Net}_{t-1}) / \text{Net}_{t-1}] \times 100$ | Period velocity calculated via `LAG` analytical window function. |

---

## 4. Before-and-After Reconciliation Matrix

### All-Time Ground Truth Comparison ($5,200$ Orders)

| Metric | Single-Table Ground Truth | Before (Buggy Join) | After (Refactored CTE) | Error Eliminated | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| **Total Orders** | 5,200 | 5,200 | **5,200** | $0$ | **MATCH** |
| **Gross Revenue** | $38,625,502.00 | $38,625,502.00 | **$38,625,502.00** | $0.00 | **MATCH** |
| **Total Discounts** | $2,342,815.06 | $2,342,815.06 | **$2,342,815.06** | $0.00 | **MATCH** |
| **Total Refunds** | **$1,261,629.33** | **$2,404,164.54** | **$1,261,629.33** | **-$1,142,535.21** (1.91x fix) | **EXACT MATCH** |
| **Net Realized Revenue** | **$35,021,057.61** | **$33,878,522.40** | **$35,021,057.61** | **+$1,142,535.21** | **EXACT MATCH** |
| **Total COGS** | $21,138,510.00 | $21,138,510.00 | **$21,138,510.00** | $0.00 | **MATCH** |
| **Gross Profit** | **$13,882,547.61** | **$12,740,012.40** | **$13,882,547.61** | **+$1,142,535.21** | **EXACT MATCH** |
| **Profit Margin** | **39.64%** | **37.60%** | **39.64%** | **+2.04%** | **EXACT MATCH** |
| **Average Order Value** | **$6,734.82** | **$6,515.10** | **$6,734.82** | **+$219.72** | **EXACT MATCH** |

---

## 5. Reconciling Database and Frontend Mock Data

The initial audit noted differences between frontend mock metrics and raw database counts:
- **Database Refunds**: 410 records ($1,261,629.33)
- **Frontend Mock Refunds**: 390 records ($779,159.95)

### Root Cause Analysis
1. **Timeline Scope**:
   - The SQLite database contains an 18-month history spanning from **May 23, 2025** through **November 14, 2026** ($5,200$ orders).
   - In contrast, the frontend mock dataset was drafted as a synthetic, normalized static 12-month calendar snapshot.
2. **Calendar Year 2026 Ground Truth**:
   - When filtering the database strictly for calendar year 2026 (`>= 2026-01-01`), the database yields **265 refunds totaling $777,162.23**, which closely aligns with the mock dataset's $779,159.95.
3. **Trailing 12 Months Ground Truth**:
   - The trailing 12-month window (`2025-11-14` to `2026-11-14`) yields **300 refunds totaling $917,511.73**.
4. **Resolution Strategy**:
   - The frontend mock data will remain intact during backend development.
   - When Phase 2, Milestone 5 cutover occurs, the frontend will seamlessly bind to the real live database figures provided by the refactored endpoints.

---

## 6. Automated Test Suite Results

Test execution output from `tests/test_analytics_validation.py`:

```
Ran 9 tests in 0.114s

OK
```

### Verified Test Cases:
1. `test_01_ground_truth_baseline_sanity`: Confirmed all-time ground-truth values across 5,200 orders.
2. `test_02_kpi_summary_query_no_fanout`: Validated zero Cartesian fan-out and exact equality between `KPI_SUMMARY_QUERY` and ground-truth metrics.
3. `test_03_monthly_aggregation_reconciliation`: Confirmed the sum of all monthly buckets equals the company all-time net revenue, gross revenue, refunds, and order counts.
4. `test_04_quarterly_aggregation`: Validated quarterly grouping and period-over-period growth velocity rates.
5. `test_05_category_breakdown_reconciliation`: Confirmed category breakdown percentages sum to exactly 100.0% and category net revenues reconcile to company net revenue.
6. `test_06_regional_breakdown_reconciliation`: Confirmed regional sales, refunds, and profit margins match company totals.
7. `test_07_customer_segmentation_reconciliation`: Confirmed customer cohort segmentation sums to total net revenue.
8. `test_08_empty_date_boundary_filtering`: Verified that out-of-range date queries return exactly 0 units sold and $0.00 revenue with no phantom records.
9. `test_09_discount_and_refund_reason_analysis`: Confirmed discount strategy totals and refund root-cause distributions sum to 100%.

---

## 7. Milestone 1 Completion & Approval Gate

Milestone 1 is **100% complete**:
- The Cartesian join fan-out bug is permanently resolved.
- Financial formulas are standardized and mathematically verified.
- The automated test suite passes with 0 errors.
- The database remains intact and preserved.

**Standing by for user approval before proceeding to Milestone 2 (Route Endpoint Normalization & Schema Verification).**
