"""
RevenueGuard SQL Analytical Queries Engine
===========================================
Enterprise-grade SQL queries using Common Table Expressions (CTEs),
Window Functions (LAG, RANK, DENSE_RANK), Multi-table JOINS, and Group By Aggregations.
Dual compatible with PostgreSQL and SQLite through dialect-aware resolvers.
"""

# 1. Total and Net Revenue with Period Comparison (CTE + Pre-Aggregations)
# Fully ANSI SQL compliant across SQLite and PostgreSQL
KPI_SUMMARY_QUERY = """
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
),
prev_items AS (
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
prev_refunds AS (
    SELECT
        r.order_id,
        COALESCE(SUM(r.refund_amount), 0.0) AS total_refunds
    FROM refunds r
    JOIN order_items oi ON r.order_item_id = oi.id
    JOIN products p ON oi.product_id = p.id
    WHERE (:category_id IS NULL OR p.category_id = :category_id)
    GROUP BY r.order_id
),
previous_period AS (
    SELECT
        COUNT(DISTINCT o.id) AS total_orders,
        COALESCE(SUM(pi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(pi.total_discounts), 0.0) AS total_discounts,
        COALESCE(SUM(pr.total_refunds), 0.0) AS total_refunds,
        (COALESCE(SUM(pi.net_revenue), 0.0) - COALESCE(SUM(pr.total_refunds), 0.0)) AS net_revenue,
        COALESCE(SUM(pi.total_cogs), 0.0) AS total_cogs,
        (COALESCE(SUM(pi.net_revenue), 0.0) - COALESCE(SUM(pr.total_refunds), 0.0) - COALESCE(SUM(pi.total_cogs), 0.0)) AS gross_profit
    FROM orders o
    JOIN prev_items pi ON o.id = pi.order_id
    LEFT JOIN prev_refunds pr ON o.id = pr.order_id
    WHERE o.order_date >= :prev_start_date AND o.order_date <= :prev_end_date
      AND (:region_id IS NULL OR o.region_id = :region_id)
)
SELECT 
    c.total_orders AS cur_orders,
    c.gross_revenue AS cur_gross_revenue,
    c.total_discounts AS cur_discounts,
    c.total_refunds AS cur_refunds,
    c.net_revenue AS cur_net_revenue,
    c.gross_profit AS cur_profit,
    p.total_orders AS prev_orders,
    p.gross_revenue AS prev_gross_revenue,
    p.total_discounts AS prev_discounts,
    p.total_refunds AS prev_refunds,
    p.net_revenue AS prev_net_revenue,
    p.gross_profit AS prev_profit
FROM current_period c, previous_period p;
"""

# 2. Monthly Revenue Trend with Window Function Growth Calculation (LAG)
# SQLite Variant: uses substr(o.order_date, 1, 7)
MONTHLY_REVENUE_TREND_QUERY_SQLITE = """
WITH order_items_agg AS (
    SELECT
        oi.order_id,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.discount_amount), 0.0) AS total_discounts,
        COALESCE(SUM(oi.net_revenue), 0.0) AS net_revenue_pre_refund,
        COALESCE(SUM(oi.cogs), 0.0) AS total_cogs
    FROM order_items oi
    GROUP BY oi.order_id
),
order_refunds_agg AS (
    SELECT
        r.order_id,
        COALESCE(SUM(r.refund_amount), 0.0) AS total_refunds
    FROM refunds r
    GROUP BY r.order_id
),
monthly_data AS (
    SELECT
        substr(o.order_date, 1, 7) AS month_period,
        COUNT(DISTINCT o.id) AS orders_count,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.total_discounts), 0.0) AS total_discounts,
        COALESCE(SUM(orf.total_refunds), 0.0) AS total_refunds,
        (COALESCE(SUM(oi.net_revenue_pre_refund), 0.0) - COALESCE(SUM(orf.total_refunds), 0.0)) AS net_revenue,
        (COALESCE(SUM(oi.net_revenue_pre_refund), 0.0) - COALESCE(SUM(orf.total_refunds), 0.0) - COALESCE(SUM(oi.total_cogs), 0.0)) AS net_profit
    FROM orders o
    JOIN order_items_agg oi ON o.id = oi.order_id
    LEFT JOIN order_refunds_agg orf ON o.id = orf.order_id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date
      AND (:region_id IS NULL OR o.region_id = :region_id)
    GROUP BY substr(o.order_date, 1, 7)
)
SELECT 
    month_period,
    orders_count,
    gross_revenue,
    total_discounts,
    total_refunds,
    net_revenue,
    net_profit,
    LAG(net_revenue, 1) OVER (ORDER BY month_period ASC) AS prev_month_net_revenue,
    CASE 
        WHEN LAG(net_revenue, 1) OVER (ORDER BY month_period ASC) IS NOT NULL AND LAG(net_revenue, 1) OVER (ORDER BY month_period ASC) > 0
        THEN ROUND(((net_revenue - LAG(net_revenue, 1) OVER (ORDER BY month_period ASC)) * 100.0 / LAG(net_revenue, 1) OVER (ORDER BY month_period ASC)), 2)
        ELSE 0.0
    END AS revenue_growth_rate
FROM monthly_data
ORDER BY month_period ASC;
"""

# PostgreSQL Variant: uses TO_CHAR(o.order_date, 'YYYY-MM') and explicit NUMERIC casting for ROUND()
MONTHLY_REVENUE_TREND_QUERY_POSTGRES = """
WITH order_items_agg AS (
    SELECT
        oi.order_id,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.discount_amount), 0.0) AS total_discounts,
        COALESCE(SUM(oi.net_revenue), 0.0) AS net_revenue_pre_refund,
        COALESCE(SUM(oi.cogs), 0.0) AS total_cogs
    FROM order_items oi
    GROUP BY oi.order_id
),
order_refunds_agg AS (
    SELECT
        r.order_id,
        COALESCE(SUM(r.refund_amount), 0.0) AS total_refunds
    FROM refunds r
    GROUP BY r.order_id
),
monthly_data AS (
    SELECT
        TO_CHAR(o.order_date, 'YYYY-MM') AS month_period,
        COUNT(DISTINCT o.id) AS orders_count,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.total_discounts), 0.0) AS total_discounts,
        COALESCE(SUM(orf.total_refunds), 0.0) AS total_refunds,
        (COALESCE(SUM(oi.net_revenue_pre_refund), 0.0) - COALESCE(SUM(orf.total_refunds), 0.0)) AS net_revenue,
        (COALESCE(SUM(oi.net_revenue_pre_refund), 0.0) - COALESCE(SUM(orf.total_refunds), 0.0) - COALESCE(SUM(oi.total_cogs), 0.0)) AS net_profit
    FROM orders o
    JOIN order_items_agg oi ON o.id = oi.order_id
    LEFT JOIN order_refunds_agg orf ON o.id = orf.order_id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date
      AND (:region_id IS NULL OR o.region_id = :region_id)
    GROUP BY TO_CHAR(o.order_date, 'YYYY-MM')
)
SELECT 
    month_period,
    orders_count,
    gross_revenue,
    total_discounts,
    total_refunds,
    net_revenue,
    net_profit,
    LAG(net_revenue, 1) OVER (ORDER BY month_period ASC) AS prev_month_net_revenue,
    CASE 
        WHEN LAG(net_revenue, 1) OVER (ORDER BY month_period ASC) IS NOT NULL AND LAG(net_revenue, 1) OVER (ORDER BY month_period ASC) > 0
        THEN ROUND(CAST(((net_revenue - LAG(net_revenue, 1) OVER (ORDER BY month_period ASC)) * 100.0 / LAG(net_revenue, 1) OVER (ORDER BY month_period ASC)) AS NUMERIC), 2)
        ELSE 0.0
    END AS revenue_growth_rate
FROM monthly_data
ORDER BY month_period ASC;
"""

# Default alias for backward compatibility
MONTHLY_REVENUE_TREND_QUERY = MONTHLY_REVENUE_TREND_QUERY_SQLITE


# 3. Top-Performing and Low-Performing Products (RANK Window Function)
PRODUCT_PERFORMANCE_QUERY = """
WITH product_stats AS (
    SELECT
        p.id AS product_id,
        p.sku,
        p.name AS product_name,
        c.name AS category_name,
        p.unit_price,
        p.unit_cost,
        COALESCE(SUM(oi.quantity), 0) AS units_sold,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.discount_amount), 0.0) AS discount_amount,
        COALESCE(SUM(oi.net_revenue), 0.0) AS net_revenue,
        COALESCE(SUM(oi.cogs), 0.0) AS total_cogs,
        COALESCE(SUM(r.refund_amount), 0.0) AS refund_amount,
        (COALESCE(SUM(oi.net_revenue), 0.0) - COALESCE(SUM(r.refund_amount), 0.0) - COALESCE(SUM(oi.cogs), 0.0)) AS profit
    FROM products p
    JOIN categories c ON p.category_id = c.id
    LEFT JOIN (
        order_items oi 
        JOIN orders o ON oi.order_id = o.id AND o.order_date >= :start_date AND o.order_date <= :end_date
    ) ON p.id = oi.product_id
    LEFT JOIN refunds r ON oi.id = r.order_item_id
    WHERE (:category_id IS NULL OR p.category_id = :category_id)
    GROUP BY p.id, p.sku, p.name, c.name, p.unit_price, p.unit_cost
)
SELECT 
    product_id,
    sku,
    product_name,
    category_name,
    unit_price,
    unit_cost,
    units_sold,
    gross_revenue,
    discount_amount,
    (net_revenue - refund_amount) AS final_net_revenue,
    refund_amount,
    profit,
    CASE 
        WHEN (net_revenue - refund_amount) > 0 
        THEN ROUND(CAST((profit * 100.0 / (net_revenue - refund_amount)) AS NUMERIC), 2) 
        ELSE 0.0 
    END AS profit_margin,
    CASE 
        WHEN gross_revenue > 0 
        THEN ROUND(CAST((discount_amount * 100.0 / gross_revenue) AS NUMERIC), 2) 
        ELSE 0.0 
    END AS discount_rate,
    CASE 
        WHEN gross_revenue > 0 
        THEN ROUND(CAST((refund_amount * 100.0 / gross_revenue) AS NUMERIC), 2) 
        ELSE 0.0 
    END AS refund_rate,
    RANK() OVER (ORDER BY (net_revenue - refund_amount) DESC) AS revenue_rank
FROM product_stats
ORDER BY final_net_revenue DESC
LIMIT :limit;
"""

# 4. Category-Wise Revenue and Contribution
CATEGORY_PERFORMANCE_QUERY = """
WITH category_metrics AS (
    SELECT
        c.id AS category_id,
        c.name AS category_name,
        COUNT(DISTINCT o.id) AS orders_count,
        COALESCE(SUM(oi.quantity), 0) AS units_sold,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.discount_amount), 0.0) AS discount_amount,
        COALESCE(SUM(oi.net_revenue), 0.0) AS net_revenue,
        COALESCE(SUM(oi.cogs), 0.0) AS total_cogs,
        COALESCE(SUM(r.refund_amount), 0.0) AS refund_amount
    FROM categories c
    JOIN products p ON c.id = p.category_id
    LEFT JOIN (
        order_items oi 
        JOIN orders o ON oi.order_id = o.id AND o.order_date >= :start_date AND o.order_date <= :end_date
    ) ON p.id = oi.product_id
    LEFT JOIN refunds r ON oi.id = r.order_item_id
    GROUP BY c.id, c.name
),
totals AS (
    SELECT COALESCE(SUM(net_revenue - refund_amount), 1.0) AS total_company_revenue
    FROM category_metrics
)
SELECT 
    cm.category_id,
    cm.category_name,
    cm.orders_count,
    cm.units_sold,
    cm.gross_revenue,
    cm.discount_amount,
    cm.refund_amount,
    (cm.net_revenue - cm.refund_amount) AS revenue,
    ((cm.net_revenue - cm.refund_amount) - cm.total_cogs) AS profit,
    CASE 
        WHEN t.total_company_revenue > 0 
        THEN ROUND(CAST(((cm.net_revenue - cm.refund_amount) * 100.0 / t.total_company_revenue) AS NUMERIC), 2)
        ELSE 0.0
    END AS percentage,
    CASE 
        WHEN (cm.net_revenue - cm.refund_amount) > 0 
        THEN ROUND(CAST((((cm.net_revenue - cm.refund_amount) - cm.total_cogs) * 100.0 / (cm.net_revenue - cm.refund_amount)) AS NUMERIC), 2)
        ELSE 0.0
    END AS profit_margin
FROM category_metrics cm, totals t
ORDER BY revenue DESC;
"""

# 5. Regional Performance Analysis
REGIONAL_PERFORMANCE_QUERY = """
WITH regional_stats AS (
    SELECT
        rg.id AS region_id,
        rg.name AS region_name,
        rg.country,
        rg.state,
        rg.city,
        rg.code,
        COUNT(DISTINCT o.id) AS orders_count,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.discount_amount), 0.0) AS discount_amount,
        COALESCE(SUM(oi.net_revenue), 0.0) AS net_revenue,
        COALESCE(SUM(oi.cogs), 0.0) AS total_cogs,
        COALESCE(SUM(r.refund_amount), 0.0) AS refund_amount
    FROM regions rg
    LEFT JOIN (
        orders o 
        JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN refunds r ON oi.id = r.order_item_id
    ) ON rg.id = o.region_id AND o.order_date >= :start_date AND o.order_date <= :end_date
    GROUP BY rg.id, rg.name, rg.country, rg.state, rg.city, rg.code
)
SELECT 
    region_id,
    region_name,
    country,
    state,
    city,
    code,
    orders_count,
    gross_revenue,
    discount_amount,
    refund_amount,
    (net_revenue - refund_amount) AS revenue,
    ((net_revenue - refund_amount) - total_cogs) AS profit,
    CASE 
        WHEN (net_revenue - refund_amount) > 0 
        THEN ROUND(CAST((((net_revenue - refund_amount) - total_cogs) * 100.0 / (net_revenue - refund_amount)) AS NUMERIC), 2)
        ELSE 0.0
    END AS profit_margin,
    CASE 
        WHEN gross_revenue > 0 
        THEN ROUND(CAST((refund_amount * 100.0 / gross_revenue) AS NUMERIC), 2)
        ELSE 0.0
    END AS refund_rate,
    CASE 
        WHEN gross_revenue > 0 
        THEN ROUND(CAST((discount_amount * 100.0 / gross_revenue) AS NUMERIC), 2)
        ELSE 0.0
    END AS discount_rate
FROM regional_stats
ORDER BY revenue DESC;
"""

# 6. Customer Segmentation & Purchase Patterns
CUSTOMER_SEGMENTATION_QUERY = """
WITH customer_orders AS (
    SELECT
        c.id AS customer_id,
        c.segment,
        COUNT(DISTINCT o.id) AS orders_count,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.net_revenue), 0.0) AS net_revenue,
        COALESCE(SUM(oi.cogs), 0.0) AS total_cogs,
        COALESCE(SUM(r.refund_amount), 0.0) AS refund_amount
    FROM customers c
    LEFT JOIN (
        orders o
        JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN refunds r ON oi.id = r.order_item_id
    ) ON c.id = o.customer_id AND o.order_date >= :start_date AND o.order_date <= :end_date
    GROUP BY c.id, c.segment
)
SELECT 
    segment,
    COUNT(customer_id) AS customers_count,
    COALESCE(SUM(orders_count), 0) AS orders_count,
    COALESCE(SUM(net_revenue - refund_amount), 0.0) AS revenue,
    COALESCE(SUM((net_revenue - refund_amount) - total_cogs), 0.0) AS profit,
    COALESCE(SUM(refund_amount), 0.0) AS refund_amount,
    CASE 
        WHEN SUM(orders_count) > 0 
        THEN ROUND(CAST(SUM(net_revenue - refund_amount) / SUM(orders_count) AS NUMERIC), 2)
        ELSE 0.0
    END AS average_order_value,
    CASE 
        WHEN COUNT(customer_id) > 0 
        THEN ROUND(CAST(SUM(CASE WHEN orders_count > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(customer_id) AS NUMERIC), 2)
        ELSE 0.0
    END AS repeat_rate
FROM customer_orders
GROUP BY segment
ORDER BY revenue DESC;
"""

# 7. Discount Impact Analysis
DISCOUNT_ANALYSIS_QUERY = """
SELECT 
    d.discount_type,
    d.discount_code,
    COUNT(DISTINCT d.order_id) AS orders_count,
    ROUND(CAST(AVG(d.discount_percentage) AS NUMERIC), 2) AS avg_discount_pct,
    ROUND(CAST(SUM(d.discount_amount) AS NUMERIC), 2) AS total_discount,
    ROUND(CAST(SUM(oi.gross_revenue) AS NUMERIC), 2) AS revenue_before,
    ROUND(CAST(SUM(oi.net_revenue) AS NUMERIC), 2) AS revenue_after,
    ROUND(CAST(SUM(d.discount_amount) AS NUMERIC), 2) AS profit_impact
FROM discounts d
JOIN orders o ON d.order_id = o.id
JOIN order_items oi ON d.order_item_id = oi.id
WHERE o.order_date >= :start_date AND o.order_date <= :end_date
GROUP BY d.discount_type, d.discount_code
ORDER BY total_discount DESC;
"""

# 8. Refund Analysis & Reasons
REFUND_ANALYSIS_QUERY = """
WITH refund_summary AS (
    SELECT 
        r.refund_reason AS reason,
        COUNT(r.id) AS count,
        ROUND(CAST(SUM(r.refund_amount) AS NUMERIC), 2) AS total_amount,
        ROUND(CAST(AVG(r.refund_amount) AS NUMERIC), 2) AS avg_amount
    FROM refunds r
    JOIN orders o ON r.order_id = o.id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date
    GROUP BY r.refund_reason
),
total_refunded AS (
    SELECT COALESCE(SUM(total_amount), 1.0) AS grand_total
    FROM refund_summary
)
SELECT 
    rs.reason,
    rs.count,
    rs.total_amount,
    rs.avg_amount,
    CASE 
        WHEN tr.grand_total > 0 
        THEN ROUND(CAST((rs.total_amount * 100.0 / tr.grand_total) AS NUMERIC), 2)
        ELSE 0.0
    END AS percentage
FROM refund_summary rs, total_refunded tr
ORDER BY rs.total_amount DESC;
"""

# 9. Recent Detailed Transactions Query
# SQLite Variant: uses GROUP_CONCAT(p.name, ', ')
RECENT_TRANSACTIONS_QUERY_SQLITE = """
SELECT 
    o.id AS order_id,
    o.order_number,
    o.order_date,
    c.name AS customer_name,
    c.segment AS customer_segment,
    GROUP_CONCAT(p.name, ', ') AS product_summary,
    ROUND(COALESCE(SUM(oi.gross_revenue), 0.0), 2) AS gross_revenue,
    ROUND(COALESCE(SUM(oi.discount_amount), 0.0), 2) AS discount_amount,
    ROUND(COALESCE(SUM(r.refund_amount), 0.0), 2) AS refund_amount,
    ROUND(COALESCE(SUM(oi.net_revenue), 0.0) - COALESCE(SUM(r.refund_amount), 0.0), 2) AS net_amount,
    o.status,
    o.payment_method
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
LEFT JOIN refunds r ON oi.id = r.order_item_id
WHERE (:search IS NULL OR o.order_number LIKE :search OR c.name LIKE :search)
GROUP BY o.id, o.order_number, o.order_date, c.name, c.segment, o.status, o.payment_method
ORDER BY o.order_date DESC
LIMIT :limit OFFSET :offset;
"""

# PostgreSQL Variant: uses STRING_AGG(p.name, ', ') and explicit NUMERIC casts
RECENT_TRANSACTIONS_QUERY_POSTGRES = """
SELECT 
    o.id AS order_id,
    o.order_number,
    o.order_date,
    c.name AS customer_name,
    c.segment AS customer_segment,
    STRING_AGG(p.name, ', ') AS product_summary,
    ROUND(CAST(COALESCE(SUM(oi.gross_revenue), 0.0) AS NUMERIC), 2) AS gross_revenue,
    ROUND(CAST(COALESCE(SUM(oi.discount_amount), 0.0) AS NUMERIC), 2) AS discount_amount,
    ROUND(CAST(COALESCE(SUM(r.refund_amount), 0.0) AS NUMERIC), 2) AS refund_amount,
    ROUND(CAST(COALESCE(SUM(oi.net_revenue), 0.0) - COALESCE(SUM(r.refund_amount), 0.0) AS NUMERIC), 2) AS net_amount,
    o.status,
    o.payment_method
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
LEFT JOIN refunds r ON oi.id = r.order_item_id
WHERE (:search IS NULL OR o.order_number LIKE :search OR c.name LIKE :search)
GROUP BY o.id, o.order_number, o.order_date, c.name, c.segment, o.status, o.payment_method
ORDER BY o.order_date DESC
LIMIT :limit OFFSET :offset;
"""

# Default alias for backward compatibility
RECENT_TRANSACTIONS_QUERY = RECENT_TRANSACTIONS_QUERY_SQLITE


def get_query(query_name: str, dialect: str = "sqlite") -> str:
    """
    Returns dialect-optimized SQL query string.
    Supports 'sqlite' and 'postgresql' / 'postgres'.
    Defaults to SQLite for backward compatibility.
    """
    dialect_clean = (dialect or "sqlite").lower()
    is_postgres = "postgres" in dialect_clean or "psql" in dialect_clean

    if query_name == "MONTHLY_REVENUE_TREND_QUERY":
        return MONTHLY_REVENUE_TREND_QUERY_POSTGRES if is_postgres else MONTHLY_REVENUE_TREND_QUERY_SQLITE

    if query_name == "RECENT_TRANSACTIONS_QUERY":
        return RECENT_TRANSACTIONS_QUERY_POSTGRES if is_postgres else RECENT_TRANSACTIONS_QUERY_SQLITE

    queries = {
        "KPI_SUMMARY_QUERY": KPI_SUMMARY_QUERY,
        "PRODUCT_PERFORMANCE_QUERY": PRODUCT_PERFORMANCE_QUERY,
        "CATEGORY_PERFORMANCE_QUERY": CATEGORY_PERFORMANCE_QUERY,
        "REGIONAL_PERFORMANCE_QUERY": REGIONAL_PERFORMANCE_QUERY,
        "CUSTOMER_SEGMENTATION_QUERY": CUSTOMER_SEGMENTATION_QUERY,
        "DISCOUNT_ANALYSIS_QUERY": DISCOUNT_ANALYSIS_QUERY,
        "REFUND_ANALYSIS_QUERY": REFUND_ANALYSIS_QUERY,
    }
    return queries.get(query_name, "")
