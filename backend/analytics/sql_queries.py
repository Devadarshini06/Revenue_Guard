"""
RevenueGuard SQL Analytical Queries Engine
===========================================
Enterprise-grade SQL queries using Common Table Expressions (CTEs),
Window Functions (LAG, RANK, DENSE_RANK), Multi-table JOINS, and Group By Aggregations.
Dual compatible with PostgreSQL and SQLite.
"""

# 1. Total and Net Revenue with Period Comparison (CTE + Aggregations)
KPI_SUMMARY_QUERY = """
WITH current_period AS (
    SELECT
        COUNT(DISTINCT o.id) AS total_orders,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.discount_amount), 0.0) AS total_discounts,
        COALESCE(SUM(r.refund_amount), 0.0) AS total_refunds,
        COALESCE(SUM(oi.net_revenue), 0.0) - COALESCE(SUM(r.refund_amount), 0.0) AS net_revenue,
        COALESCE(SUM(oi.cogs), 0.0) AS total_cogs,
        (COALESCE(SUM(oi.net_revenue), 0.0) - COALESCE(SUM(r.refund_amount), 0.0) - COALESCE(SUM(oi.cogs), 0.0)) AS gross_profit
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN refunds r ON o.id = r.order_id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date
      AND (:region_id IS NULL OR o.region_id = :region_id)
      AND (:category_id IS NULL OR oi.product_id IN (SELECT id FROM products WHERE category_id = :category_id))
),
previous_period AS (
    SELECT
        COUNT(DISTINCT o.id) AS total_orders,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.discount_amount), 0.0) AS total_discounts,
        COALESCE(SUM(r.refund_amount), 0.0) AS total_refunds,
        COALESCE(SUM(oi.net_revenue), 0.0) - COALESCE(SUM(r.refund_amount), 0.0) AS net_revenue,
        COALESCE(SUM(oi.cogs), 0.0) AS total_cogs,
        (COALESCE(SUM(oi.net_revenue), 0.0) - COALESCE(SUM(r.refund_amount), 0.0) - COALESCE(SUM(oi.cogs), 0.0)) AS gross_profit
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN refunds r ON o.id = r.order_id
    WHERE o.order_date >= :prev_start_date AND o.order_date <= :prev_end_date
      AND (:region_id IS NULL OR o.region_id = :region_id)
      AND (:category_id IS NULL OR oi.product_id IN (SELECT id FROM products WHERE category_id = :category_id))
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
MONTHLY_REVENUE_TREND_QUERY = """
WITH monthly_data AS (
    SELECT
        substr(o.order_date, 1, 7) AS month_period,
        COUNT(DISTINCT o.id) AS orders_count,
        COALESCE(SUM(oi.gross_revenue), 0.0) AS gross_revenue,
        COALESCE(SUM(oi.discount_amount), 0.0) AS total_discounts,
        COALESCE(SUM(oi.net_revenue), 0.0) AS net_revenue_pre_refund,
        COALESCE(SUM(oi.cogs), 0.0) AS total_cogs
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    WHERE o.order_date >= :start_date AND o.order_date <= :end_date
      AND (:region_id IS NULL OR o.region_id = :region_id)
    GROUP BY substr(o.order_date, 1, 7)
),
monthly_refunds AS (
    SELECT
        substr(r.refund_date, 1, 7) AS month_period,
        COALESCE(SUM(r.refund_amount), 0.0) AS total_refunds
    FROM refunds r
    WHERE r.refund_date >= :start_date AND r.refund_date <= :end_date
    GROUP BY substr(r.refund_date, 1, 7)
),
aggregated AS (
    SELECT
        m.month_period,
        m.orders_count,
        m.gross_revenue,
        m.total_discounts,
        COALESCE(rf.total_refunds, 0.0) AS total_refunds,
        (m.net_revenue_pre_refund - COALESCE(rf.total_refunds, 0.0)) AS net_revenue,
        (m.net_revenue_pre_refund - COALESCE(rf.total_refunds, 0.0) - m.total_cogs) AS net_profit
    FROM monthly_data m
    LEFT JOIN monthly_refunds rf ON m.month_period = rf.month_period
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
FROM aggregated
ORDER BY month_period ASC;
"""

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
    LEFT JOIN order_items oi ON p.id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.id AND o.order_date >= :start_date AND o.order_date <= :end_date
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
        THEN ROUND((profit * 100.0 / (net_revenue - refund_amount)), 2) 
        ELSE 0.0 
    END AS profit_margin,
    CASE 
        WHEN gross_revenue > 0 
        THEN ROUND((discount_amount * 100.0 / gross_revenue), 2) 
        ELSE 0.0 
    END AS discount_rate,
    CASE 
        WHEN gross_revenue > 0 
        THEN ROUND((refund_amount * 100.0 / gross_revenue), 2) 
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
    LEFT JOIN order_items oi ON p.id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.id AND o.order_date >= :start_date AND o.order_date <= :end_date
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
    ROUND(((cm.net_revenue - cm.refund_amount) * 100.0 / t.total_company_revenue), 2) AS percentage,
    CASE 
        WHEN (cm.net_revenue - cm.refund_amount) > 0 
        THEN ROUND((((cm.net_revenue - cm.refund_amount) - cm.total_cogs) * 100.0 / (cm.net_revenue - cm.refund_amount)), 2)
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
    LEFT JOIN orders o ON rg.id = o.region_id AND o.order_date >= :start_date AND o.order_date <= :end_date
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN refunds r ON oi.id = r.order_item_id
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
        THEN ROUND((((net_revenue - refund_amount) - total_cogs) * 100.0 / (net_revenue - refund_amount)), 2)
        ELSE 0.0
    END AS profit_margin,
    CASE 
        WHEN gross_revenue > 0 
        THEN ROUND((refund_amount * 100.0 / gross_revenue), 2)
        ELSE 0.0
    END AS refund_rate,
    CASE 
        WHEN gross_revenue > 0 
        THEN ROUND((discount_amount * 100.0 / gross_revenue), 2)
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
    LEFT JOIN orders o ON c.id = o.customer_id AND o.order_date >= :start_date AND o.order_date <= :end_date
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN refunds r ON oi.id = r.order_item_id
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
        THEN ROUND(SUM(net_revenue - refund_amount) / SUM(orders_count), 2)
        ELSE 0.0
    END AS average_order_value,
    CASE 
        WHEN COUNT(customer_id) > 0 
        THEN ROUND(SUM(CASE WHEN orders_count > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(customer_id), 2)
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
    ROUND(AVG(d.discount_percentage), 2) AS avg_discount_pct,
    ROUND(SUM(d.discount_amount), 2) AS total_discount,
    ROUND(SUM(oi.gross_revenue), 2) AS revenue_before,
    ROUND(SUM(oi.net_revenue), 2) AS revenue_after,
    ROUND(SUM(d.discount_amount), 2) AS profit_impact
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
        ROUND(SUM(r.refund_amount), 2) AS total_amount,
        ROUND(AVG(r.refund_amount), 2) AS avg_amount
    FROM refunds r
    WHERE r.refund_date >= :start_date AND r.refund_date <= :end_date
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
    ROUND((rs.total_amount * 100.0 / tr.grand_total), 2) AS percentage
FROM refund_summary rs, total_refunded tr
ORDER BY rs.total_amount DESC;
"""

# 9. Recent Detailed Transactions Query
RECENT_TRANSACTIONS_QUERY = """
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

