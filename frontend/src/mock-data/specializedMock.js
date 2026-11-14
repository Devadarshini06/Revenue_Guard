import { MOCK_CATEGORIES_BREAKDOWN, MOCK_TOP_PRODUCTS, MOCK_REGIONAL_SALES, MOCK_RECENT_TRANSACTIONS } from './overviewMock';

// Sales Performance
export const MOCK_SALES_SUMMARY = {
  total_orders: 5200,
  total_units_sold: 8800,
  total_sales: 24980392.55,
  average_order_value: 4803.92
};

export const MOCK_PAYMENT_METHODS = [
  { payment_method: 'Credit Card', orders_count: 2340, total_amount: 11241176.65, avg_amount: 4803.92 },
  { payment_method: 'Wire Transfer', orders_count: 1820, total_amount: 8743137.40, avg_amount: 4803.92 },
  { payment_method: 'ACH', orders_count: 780, total_amount: 3747058.88, avg_amount: 4803.92 },
  { payment_method: 'PayPal', orders_count: 260, total_amount: 1249019.62, avg_amount: 4803.92 }
];

// Discount Analysis
export const MOCK_DISCOUNT_SUMMARY = {
  total_discounts: 1720840.00,
  total_instances: 1980,
  average_discount_percentage: 16.4,
  revenue_erosion_rate: 6.26
};

export const MOCK_DISCOUNT_TYPES = [
  { discount_type: 'Volume', discount_code: 'ENTERPRISE20', orders_count: 650, avg_discount_pct: 20.0, total_discount: 620000.0, revenue_before: 3100000.0, revenue_after: 2480000.0, profit_impact: 620000.0 },
  { discount_type: 'Volume', discount_code: 'MIDMARKET15', orders_count: 510, avg_discount_pct: 15.0, total_discount: 410000.0, revenue_before: 2733333.3, revenue_after: 2323333.3, profit_impact: 410000.0 },
  { discount_type: 'Partner', discount_code: 'TECHPARTNER', orders_count: 320, avg_discount_pct: 18.0, total_discount: 280000.0, revenue_before: 1555555.5, revenue_after: 1275555.5, profit_impact: 280000.0 },
  { discount_type: 'Promotional', discount_code: 'GROWTH10', orders_count: 290, avg_discount_pct: 10.0, total_discount: 220840.0, revenue_before: 2208400.0, revenue_after: 1987560.0, profit_impact: 220840.0 },
  { discount_type: 'Retention', discount_code: 'RETENTION25', orders_count: 210, avg_discount_pct: 25.0, total_discount: 190000.0, revenue_before: 760000.0, revenue_after: 570000.0, profit_impact: 190000.0 }
];

export const MOCK_CATEGORY_DISCOUNTS = [
  { category_name: 'Cloud & Infrastructure', gross_revenue: 9240000.0, discount_amount: 580000.0, discount_percentage: 6.28 },
  { category_name: 'Cybersecurity & Compliance', gross_revenue: 7850000.0, discount_amount: 470000.0, discount_percentage: 5.99 },
  { category_name: 'Data Analytics & AI', gross_revenue: 5320000.0, discount_amount: 340000.0, discount_percentage: 6.39 },
  { category_name: 'Hardware Appliances', gross_revenue: 3120000.0, discount_amount: 190000.0, discount_percentage: 6.09 },
  { category_name: 'Professional Services', gross_revenue: 1950392.0, discount_amount: 140840.0, discount_percentage: 7.22 }
];

export const MOCK_HIGH_DISCOUNT_ORDERS = [
  { order_number: 'ORD-2026-004819', order_date: '2026-10-28', customer_name: 'Apex Global Financial', product_name: 'Dedicated Kubernetes Cluster', reason: 'Annual Enterprise Volume Commit', gross_revenue: 14990.0, discount_percentage: 20.0, discount_amount: 2998.0, net_revenue: 11992.0, profit: 4792.0 },
  { order_number: 'ORD-2026-004752', order_date: '2026-10-22', customer_name: 'Vanguard Health Systems', product_name: 'Endpoint Threat Detection (500 seats)', reason: 'Strategic Cloud Partner Rebate', gross_revenue: 17500.0, discount_percentage: 18.0, discount_amount: 3150.0, net_revenue: 14350.0, profit: 7350.0 },
  { order_number: 'ORD-2026-004610', order_date: '2026-10-15', customer_name: 'Summit Biometrics Ltd', product_name: 'Enterprise Virtual Private Cloud', reason: 'Contract Renewal Concession', gross_revenue: 11000.0, discount_percentage: 25.0, discount_amount: 2750.0, net_revenue: 8250.0, profit: 3300.0 },
  { order_number: 'ORD-2026-004520', order_date: '2026-10-09', customer_name: 'Nexus Cloud Robotics', product_name: 'Zero-Trust Perimeter Shield', reason: 'Annual Enterprise Volume Commit', gross_revenue: 9250.0, discount_percentage: 20.0, discount_amount: 1850.0, net_revenue: 7400.0, profit: 4150.0 },
  { order_number: 'ORD-2026-004388', order_date: '2026-09-29', customer_name: 'Quantum Edge Labs', product_name: 'Real-Time Event Ingestion Pipeline', reason: 'Mid-Market Tier Discount', gross_revenue: 6250.0, discount_percentage: 15.0, discount_amount: 937.5, net_revenue: 5312.5, profit: 2812.5 }
];

// Refund Analysis
export const MOCK_REFUND_SUMMARY = {
  total_refund_amount: 779159.95,
  total_refunds_count: 395,
  refunded_orders_count: 390,
  refund_rate: 2.84
};

export const MOCK_REFUND_REASONS = [
  { reason: 'Defective Item', count: 142, total_amount: 266472.0, avg_amount: 1876.56, percentage: 34.2 },
  { reason: 'Customer Cancellation', count: 98, total_amount: 194789.98, avg_amount: 1987.65, percentage: 25.0 },
  { reason: 'Pricing Discrepancy', count: 71, total_amount: 140248.79, avg_amount: 1975.33, percentage: 18.0 },
  { reason: 'Late Delivery', count: 47, total_amount: 93499.19, avg_amount: 1989.34, percentage: 12.0 },
  { reason: 'Incorrect Product', count: 37, total_amount: 84150.0, avg_amount: 2274.32, percentage: 10.8 }
];

export const MOCK_HIGH_REFUND_PRODUCTS = [
  { product_id: 14, sku: 'PRD-HW-02', product_name: 'FIPS 140-3 Hardware Security Module', category_name: 'Hardware Appliances', refund_claims: 28, gross_sales: 1566000.0, total_refunded: 40000.0, refund_rate: 2.55 },
  { product_id: 13, sku: 'PRD-HW-01', product_name: 'Edge Telemetry Gateway 10Gbps', category_name: 'Hardware Appliances', refund_claims: 24, gross_sales: 1216000.0, total_refunded: 30000.0, refund_rate: 2.47 },
  { product_id: 8, sku: 'PRD-SEC-04', product_name: 'Endpoint Threat Detection (500 seats)', category_name: 'Cybersecurity & Compliance', refund_claims: 19, gross_sales: 2380000.0, total_refunded: 50000.0, refund_rate: 2.10 },
  { product_id: 1, sku: 'PRD-CLD-01', product_name: 'Dedicated Kubernetes Cluster', category_name: 'Cloud & Infrastructure', refund_claims: 22, gross_sales: 2758160.0, total_refunded: 50000.0, refund_rate: 1.81 },
  { product_id: 11, sku: 'PRD-DAT-03', product_name: 'Predictive Churn Engine Subscription', category_name: 'Data Analytics & AI', refund_claims: 18, gross_sales: 1701000.0, total_refunded: 30000.0, refund_rate: 1.76 }
];

// Profitability Analysis
export const MOCK_PROFIT_SUMMARY = {
  gross_revenue: 27480392.50,
  discounts: 1720840.00,
  refunds: 779159.95,
  net_revenue: 24980392.55,
  cost_of_goods_sold: 15684652.45,
  gross_profit: 9295740.10,
  profit_margin: 37.21
};

export const MOCK_PRODUCT_QUADRANT = MOCK_TOP_PRODUCTS.map(p => {
  let classification = 'Star (High Revenue, High Margin)';
  if (p.revenue > 1800000 && p.profit_margin < 40) classification = 'Workhorse (High Revenue, Low Margin)';
  else if (p.revenue <= 1800000 && p.profit_margin >= 40) classification = 'Niche Opportunity (Low Revenue, High Margin)';
  else if (p.revenue <= 1800000 && p.profit_margin < 40) classification = 'Underperformer (Low Revenue, Low Margin)';

  return {
    ...p,
    classification,
    is_high_revenue: p.revenue > 1800000,
    is_high_margin: p.profit_margin >= 40
  };
});

// Customer Insights
export const MOCK_CUSTOMER_SUMMARY = {
  total_customers: 350,
  active_orders: 5200,
  total_revenue: 24980392.55,
  average_customer_spending: 71372.55
};

export const MOCK_CUSTOMER_SEGMENTS = [
  { segment: 'Enterprise', customers_count: 88, orders_count: 2280, revenue: 13739215.90, profit: 5112657.06, refund_amount: 428537.97, average_order_value: 6025.97, repeat_rate: 96.5 },
  { segment: 'Mid-Market', customers_count: 122, orders_count: 1640, revenue: 6994509.91, profit: 2602807.23, refund_amount: 218164.79, average_order_value: 4264.95, repeat_rate: 94.2 },
  { segment: 'SMB', customers_count: 105, orders_count: 1040, revenue: 3497254.96, profit: 1301403.61, refund_amount: 109082.39, average_order_value: 3362.75, repeat_rate: 91.4 },
  { segment: 'Direct Consumer', customers_count: 35, orders_count: 240, revenue: 749411.78, profit: 278872.20, refund_amount: 23374.80, average_order_value: 3122.55, repeat_rate: 88.5 }
];

export const MOCK_TOP_CUSTOMERS = [
  { id: 1, customer_code: 'CUST-00001', name: 'Apex Global Financial', segment: 'Enterprise', email: 'billing@apexfinancial.com', region_name: 'North America - East', total_orders: 42, total_spent: 318500.0, refund_total: 0.0 },
  { id: 2, customer_code: 'CUST-00002', name: 'Vanguard Health Systems', segment: 'Enterprise', email: 'procurement@vanguardhealth.com', region_name: 'North America - West', total_orders: 38, total_spent: 294000.0, refund_total: 12000.0 },
  { id: 3, customer_code: 'CUST-00003', name: 'Crestline Aerospace Group', segment: 'Enterprise', email: 'finance@crestlineaero.com', region_name: 'North America - Central', total_orders: 35, total_spent: 271250.0, refund_total: 0.0 },
  { id: 4, customer_code: 'CUST-00004', name: 'Quantum Edge Labs', segment: 'Enterprise', email: 'accounts@quantumedge.com', region_name: 'Europe - UK & Ireland', total_orders: 31, total_spent: 240250.0, refund_total: 5400.0 },
  { id: 5, customer_code: 'CUST-00005', name: 'Nexus Cloud Robotics', segment: 'Mid-Market', email: 'orders@nexuscloud.com', region_name: 'North America - West', total_orders: 28, total_spent: 217000.0, refund_total: 3200.0 },
  { id: 6, customer_code: 'CUST-00006', name: 'Borealis Media Network', segment: 'Mid-Market', email: 'ap@borealismedia.com', region_name: 'Europe - Central', total_orders: 26, total_spent: 201500.0, refund_total: 0.0 },
  { id: 7, customer_code: 'CUST-00007', name: 'Summit Biometrics Ltd', segment: 'Enterprise', email: 'finance@summitbiometrics.com', region_name: 'Asia Pacific - Japan', total_orders: 24, total_spent: 186000.0, refund_total: 5400.0 },
  { id: 8, customer_code: 'CUST-00008', name: 'Aether Logistics Corp', segment: 'SMB', email: 'accounting@aetherlogistics.com', region_name: 'North America - East', total_orders: 22, total_spent: 170500.0, refund_total: 0.0 }
];

// Data Management
export const MOCK_UPLOAD_HISTORY = [
  { id: 1, filename: 'enterprise_transactions_q4_2026.csv', upload_date: '2026-11-14 10:15:20', rows_count: 5200, valid_rows: 5200, invalid_rows: 0, duplicate_rows: 0, status: 'Completed', summary_notes: 'Baseline seed dataset with 5,200 orders across 5 categories and 8 global regions.' },
  { id: 2, filename: 'partner_rebates_batch_oct.xlsx', upload_date: '2026-10-31 16:40:12', rows_count: 850, valid_rows: 846, invalid_rows: 4, duplicate_rows: 0, status: 'Completed', summary_notes: 'Data Quality Score: 98.4%. Validated 846 clean rows.' },
  { id: 3, filename: 'hardware_procurement_q3.csv', upload_date: '2026-09-30 11:22:05', rows_count: 420, valid_rows: 418, invalid_rows: 2, duplicate_rows: 0, status: 'Completed', summary_notes: 'Direct reconciliation with vendor shipping logs.' }
];

export const MOCK_VALIDATION_SAMPLE = {
  filename: 'uploaded_sample_dataset.csv',
  total_rows: 250,
  valid_rows: 248,
  invalid_rows: 2,
  duplicate_rows: 0,
  missing_columns: [],
  missing_values: { discount_code: 42 },
  column_types: {
    order_number: 'object',
    order_date: 'datetime',
    customer_code: 'object',
    product_sku: 'object',
    quantity: 'int64',
    unit_price: 'float64',
    discount_amount: 'float64'
  },
  quality_score: 99.2,
  preview: [
    { order_number: 'ORD-2026-005201', order_date: '2026-11-14', customer_code: 'CUST-00001', product_sku: 'PRD-CLD-01', quantity: 2, unit_price: 1499.0, discount_amount: 299.8 },
    { order_number: 'ORD-2026-005202', order_date: '2026-11-14', customer_code: 'CUST-00002', product_sku: 'PRD-SEC-01', quantity: 1, unit_price: 1850.0, discount_amount: 0.0 },
    { order_number: 'ORD-2026-005203', order_date: '2026-11-13', customer_code: 'CUST-00004', product_sku: 'PRD-DAT-01', quantity: 3, unit_price: 1250.0, discount_amount: 375.0 },
    { order_number: 'ORD-2026-005204', order_date: '2026-11-13', customer_code: 'CUST-00007', product_sku: 'PRD-HW-02', quantity: 1, unit_price: 5400.0, discount_amount: 0.0 }
  ]
};
