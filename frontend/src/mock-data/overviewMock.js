export const MOCK_KPIS = {
  total_revenue: {
    value: 27480392.50,
    previous_value: 23891329.85,
    change_percentage: 15.02,
    is_positive: true,
    formatted_value: '$27,480,392.50',
    formatted_change: '+15.0%'
  },
  net_revenue: {
    value: 24980392.55,
    previous_value: 21718920.40,
    change_percentage: 15.02,
    is_positive: true,
    formatted_value: '$24,980,392.55',
    formatted_change: '+15.0%'
  },
  total_orders: {
    value: 5200,
    previous_value: 4620,
    change_percentage: 12.55,
    is_positive: true,
    formatted_value: '5,200',
    formatted_change: '+12.6%'
  },
  average_order_value: {
    value: 4803.92,
    previous_value: 4701.06,
    change_percentage: 2.19,
    is_positive: true,
    formatted_value: '$4,803.92',
    formatted_change: '+2.2%'
  },
  total_discounts: {
    value: 1720840.00,
    previous_value: 1480200.00,
    change_percentage: 16.26,
    is_positive: false,
    formatted_value: '$1,720,840.00',
    formatted_change: '+16.3%'
  },
  total_refunds: {
    value: 779159.95,
    previous_value: 692209.45,
    change_percentage: 12.56,
    is_positive: false,
    formatted_value: '$779,159.95',
    formatted_change: '+12.6%'
  },
  gross_profit: {
    value: 9295740.10,
    previous_value: 8083252.26,
    change_percentage: 15.00,
    is_positive: true,
    formatted_value: '$9,295,740.10',
    formatted_change: '+15.0%'
  },
  profit_margin: {
    value: 37.21,
    previous_value: 37.22,
    change_percentage: -0.01,
    is_positive: true,
    formatted_value: '37.2%',
    formatted_change: '+0.0%'
  }
};

export const MOCK_TRENDS = [
  { date: '2025-05', label: 'May 25', gross_revenue: 1620000, net_revenue: 1480000, profit: 540000, orders_count: 310, discounts: 98000, refunds: 42000, growth_rate: 8.2 },
  { date: '2025-06', label: 'Jun 25', gross_revenue: 1750000, net_revenue: 1590000, profit: 585000, orders_count: 340, discounts: 105000, refunds: 55000, growth_rate: 7.4 },
  { date: '2025-07', label: 'Jul 25', gross_revenue: 1840000, net_revenue: 1675000, profit: 620000, orders_count: 355, discounts: 112000, refunds: 53000, growth_rate: 5.3 },
  { date: '2025-08', label: 'Aug 25', gross_revenue: 1980000, net_revenue: 1805000, profit: 672000, orders_count: 380, discounts: 119000, refunds: 56000, growth_rate: 7.8 },
  { date: '2025-09', label: 'Sep 25', gross_revenue: 2110000, net_revenue: 1920000, profit: 715000, orders_count: 405, discounts: 128000, refunds: 62000, growth_rate: 6.4 },
  { date: '2025-10', label: 'Oct 25', gross_revenue: 2260000, net_revenue: 2055000, profit: 768000, orders_count: 430, discounts: 139000, refunds: 66000, growth_rate: 7.0 },
  { date: '2025-11', label: 'Nov 25', gross_revenue: 2420000, net_revenue: 2200000, profit: 825000, orders_count: 460, discounts: 151000, refunds: 69000, growth_rate: 7.1 },
  { date: '2025-12', label: 'Dec 25', gross_revenue: 2680000, net_revenue: 2435000, profit: 915000, orders_count: 510, discounts: 172000, refunds: 73000, growth_rate: 10.7 },
  { date: '2026-01', label: 'Jan 26', gross_revenue: 2390000, net_revenue: 2180000, profit: 810000, orders_count: 450, discounts: 145000, refunds: 65000, growth_rate: -10.5 },
  { date: '2026-02', label: 'Feb 26', gross_revenue: 2490000, net_revenue: 2270000, profit: 846000, orders_count: 470, discounts: 153000, refunds: 67000, growth_rate: 4.1 },
  { date: '2026-03', label: 'Mar 26', gross_revenue: 2670000, net_revenue: 2430000, profit: 908000, orders_count: 505, discounts: 168000, refunds: 72000, growth_rate: 7.0 },
  { date: '2026-04', label: 'Apr 26', gross_revenue: 2790000, net_revenue: 2540000, profit: 948000, orders_count: 530, discounts: 175000, refunds: 75000, growth_rate: 4.5 },
  { date: '2026-05', label: 'May 26', gross_revenue: 2950000, net_revenue: 2690000, profit: 1005000, orders_count: 560, discounts: 184000, refunds: 76000, growth_rate: 5.9 }
];

export const MOCK_CATEGORIES_BREAKDOWN = [
  {
    category_id: 1,
    category_name: 'Cloud & Infrastructure',
    orders_count: 1560,
    units_sold: 2840,
    gross_revenue: 9240000,
    discount_amount: 580000,
    refund_amount: 195000,
    revenue: 8465000,
    profit: 3280000,
    percentage: 33.89,
    profit_margin: 38.75
  },
  {
    category_id: 2,
    category_name: 'Cybersecurity & Compliance',
    orders_count: 1240,
    units_sold: 2190,
    gross_revenue: 7850000,
    discount_amount: 470000,
    refund_amount: 180000,
    revenue: 7200000,
    profit: 2950000,
    percentage: 28.82,
    profit_margin: 40.97
  },
  {
    category_id: 3,
    category_name: 'Data Analytics & AI',
    orders_count: 1080,
    units_sold: 1920,
    gross_revenue: 5320000,
    discount_amount: 340000,
    refund_amount: 165000,
    revenue: 4815000,
    profit: 1780000,
    percentage: 19.27,
    profit_margin: 36.97
  },
  {
    category_id: 4,
    category_name: 'Hardware Appliances',
    orders_count: 780,
    units_sold: 1140,
    gross_revenue: 3120000,
    discount_amount: 190000,
    refund_amount: 145000,
    revenue: 2785000,
    profit: 690000,
    percentage: 11.15,
    profit_margin: 24.78
  },
  {
    category_id: 5,
    category_name: 'Professional Services & Support',
    orders_count: 540,
    units_sold: 710,
    gross_revenue: 1950392,
    discount_amount: 140840,
    refund_amount: 94160,
    revenue: 1715392,
    profit: 595740,
    percentage: 6.87,
    profit_margin: 34.73
  }
];

export const MOCK_TOP_PRODUCTS = [
  { product_id: 1, sku: 'PRD-CLD-01', name: 'Dedicated Kubernetes Cluster', category_name: 'Cloud & Infrastructure', unit_price: 1499.0, unit_cost: 720.0, units_sold: 1840, gross_revenue: 2758160, discount_amount: 165000, revenue: 2543160, refund_amount: 50000, profit: 1218360, profit_margin: 47.9, discount_rate: 5.9, refund_rate: 1.8, rank: 1 },
  { product_id: 8, sku: 'PRD-SEC-04', name: 'Endpoint Threat Detection (500 seats)', category_name: 'Cybersecurity & Compliance', unit_price: 3500.0, unit_cost: 1400.0, units_sold: 680, gross_revenue: 2380000, discount_amount: 142000, revenue: 2188000, refund_amount: 50000, profit: 1236000, profit_margin: 56.5, discount_rate: 5.9, refund_rate: 2.1, rank: 2 },
  { product_id: 4, sku: 'PRD-CLD-04', name: 'Enterprise Virtual Private Cloud', category_name: 'Cloud & Infrastructure', unit_price: 2200.0, unit_cost: 990.0, units_sold: 940, gross_revenue: 2068000, discount_amount: 124000, revenue: 1904000, refund_amount: 40000, profit: 973400, profit_margin: 51.1, discount_rate: 5.9, refund_rate: 1.9, rank: 3 },
  { product_id: 5, sku: 'PRD-SEC-01', name: 'Zero-Trust Perimeter Shield', category_name: 'Cybersecurity & Compliance', unit_price: 1850.0, unit_cost: 650.0, units_sold: 1020, gross_revenue: 1887000, discount_amount: 113000, revenue: 1734000, refund_amount: 40000, profit: 1071000, profit_margin: 61.8, discount_rate: 5.9, refund_rate: 2.1, rank: 4 },
  { product_id: 11, sku: 'PRD-DAT-03', name: 'Predictive Churn Engine Subscription', category_name: 'Data Analytics & AI', unit_price: 2100.0, unit_cost: 840.0, units_sold: 810, gross_revenue: 1701000, discount_amount: 102000, revenue: 1569000, refund_amount: 30000, profit: 888600, profit_margin: 56.6, discount_rate: 5.9, refund_rate: 1.8, rank: 5 },
  { product_id: 17, sku: 'PRD-SRV-02', name: 'Cloud Migration Sprint (40 Hours)', category_name: 'Professional Services & Support', unit_price: 6000.0, unit_cost: 3600.0, units_sold: 260, gross_revenue: 1560000, discount_amount: 93000, revenue: 1447000, refund_amount: 20000, profit: 511000, profit_margin: 35.3, discount_rate: 5.9, refund_rate: 1.3, rank: 6 },
  { product_id: 14, sku: 'PRD-HW-02', name: 'FIPS 140-3 Hardware Security Module', category_name: 'Hardware Appliances', unit_price: 5400.0, unit_cost: 4100.0, units_sold: 290, gross_revenue: 1566000, discount_amount: 94000, revenue: 1432000, refund_amount: 40000, profit: 243000, profit_margin: 17.0, discount_rate: 6.0, refund_rate: 2.6, rank: 7 },
  { product_id: 7, sku: 'PRD-SEC-03', name: 'Next-Gen AI Web Application Firewall', category_name: 'Cybersecurity & Compliance', unit_price: 1200.0, unit_cost: 420.0, units_sold: 1180, gross_revenue: 1416000, discount_amount: 85000, revenue: 1301000, refund_amount: 30000, profit: 805400, profit_margin: 61.9, discount_rate: 6.0, refund_rate: 2.1, rank: 8 },
  { product_id: 9, sku: 'PRD-DAT-01', name: 'Real-Time Event Ingestion Pipeline', category_name: 'Data Analytics & AI', unit_price: 1250.0, unit_cost: 500.0, units_sold: 1040, gross_revenue: 1300000, discount_amount: 78000, revenue: 1192000, refund_amount: 30000, profit: 672000, profit_margin: 56.4, discount_rate: 6.0, refund_rate: 2.3, rank: 9 },
  { product_id: 13, sku: 'PRD-HW-01', name: 'Edge Telemetry Gateway 10Gbps', category_name: 'Hardware Appliances', unit_price: 3200.0, unit_cost: 2400.0, units_sold: 380, gross_revenue: 1216000, discount_amount: 73000, revenue: 1113000, refund_amount: 30000, profit: 201000, profit_margin: 18.1, discount_rate: 6.0, refund_rate: 2.5, rank: 10 }
];

export const MOCK_REGIONAL_SALES = [
  { region_id: 1, region_name: 'North America - East', country: 'United States', state: 'New York', city: 'New York', code: 'NA-EAST', orders_count: 1420, gross_revenue: 7650000, discount_amount: 470000, refund_amount: 195000, revenue: 6985000, profit: 2620000, profit_margin: 37.5, refund_rate: 2.5, discount_rate: 6.1 },
  { region_id: 2, region_name: 'North America - West', country: 'United States', state: 'California', city: 'San Francisco', code: 'NA-WEST', orders_count: 1280, gross_revenue: 6890000, discount_amount: 420000, refund_amount: 180000, revenue: 6290000, profit: 2360000, profit_margin: 37.5, refund_rate: 2.6, discount_rate: 6.1 },
  { region_id: 4, region_name: 'Europe - UK & Ireland', country: 'United Kingdom', state: 'England', city: 'London', code: 'EU-WEST', orders_count: 850, gross_revenue: 4320000, discount_amount: 270000, refund_amount: 125000, revenue: 3925000, profit: 1470000, profit_margin: 37.5, refund_rate: 2.9, discount_rate: 6.2 },
  { region_id: 5, region_name: 'Europe - Central', country: 'Germany', state: 'Hesse', city: 'Frankfurt', code: 'EU-CENTRAL', orders_count: 620, gross_revenue: 3180000, discount_amount: 200000, refund_amount: 98000, revenue: 2882000, profit: 1080000, profit_margin: 37.5, refund_rate: 3.1, discount_rate: 6.3 },
  { region_id: 6, region_name: 'Asia Pacific - Japan', country: 'Japan', state: 'Kanto', city: 'Tokyo', code: 'APAC-JP', orders_count: 440, gross_revenue: 2340000, discount_amount: 150000, refund_amount: 72000, revenue: 2118000, profit: 795000, profit_margin: 37.5, refund_rate: 3.1, discount_rate: 6.4 },
  { region_id: 3, region_name: 'North America - Central', country: 'United States', state: 'Illinois', city: 'Chicago', code: 'NA-CENTRAL', orders_count: 360, gross_revenue: 1820000, discount_amount: 120000, refund_amount: 61000, revenue: 1639000, profit: 615000, profit_margin: 37.5, refund_rate: 3.3, discount_rate: 6.6 },
  { region_id: 7, region_name: 'Asia Pacific - ANZ', country: 'Australia', state: 'New South Wales', city: 'Sydney', code: 'APAC-ANZ', orders_count: 150, gross_revenue: 810000, discount_amount: 52000, refund_amount: 28000, revenue: 730000, profit: 274000, profit_margin: 37.5, refund_rate: 3.5, discount_rate: 6.4 },
  { region_id: 8, region_name: 'Latin America', country: 'Brazil', state: 'São Paulo', city: 'São Paulo', code: 'LATAM', orders_count: 80, gross_revenue: 470392, discount_amount: 38840, refund_amount: 20160, revenue: 411392, profit: 154240, profit_margin: 37.5, refund_rate: 4.3, discount_rate: 8.3 }
];

export const MOCK_RECENT_TRANSACTIONS = [
  { order_id: 5200, order_number: 'ORD-2026-005200', order_date: '2026-11-14 09:24:10', customer_name: 'Apex Global Financial', customer_segment: 'Enterprise', product_summary: 'Dedicated Kubernetes Cluster, Zero-Trust Perimeter Shield', gross_revenue: 6698.00, discount_amount: 1339.60, refund_amount: 0.00, net_amount: 5358.40, status: 'Completed', payment_method: 'Wire Transfer' },
  { order_id: 5199, order_number: 'ORD-2026-005199', order_date: '2026-11-13 18:41:22', customer_name: 'Vanguard Health Systems', customer_segment: 'Enterprise', product_summary: 'Endpoint Threat Detection (500 seats)', gross_revenue: 7000.00, discount_amount: 1050.00, refund_amount: 0.00, net_amount: 5950.00, status: 'Completed', payment_method: 'Credit Card' },
  { order_id: 5198, order_number: 'ORD-2026-005198', order_date: '2026-11-13 14:15:04', customer_name: 'Nexus Cloud Robotics', customer_segment: 'Mid-Market', product_summary: 'Edge Telemetry Gateway 10Gbps', gross_revenue: 3200.00, discount_amount: 0.00, refund_amount: 1600.00, net_amount: 1600.00, status: 'Partially_Refunded', payment_method: 'ACH' },
  { order_id: 5197, order_number: 'ORD-2026-005197', order_date: '2026-11-12 11:05:40', customer_name: 'Aether Logistics Corp', customer_segment: 'SMB', product_summary: 'Real-Time Event Ingestion Pipeline', gross_revenue: 2500.00, discount_amount: 250.00, refund_amount: 0.00, net_amount: 2250.00, status: 'Completed', payment_method: 'Credit Card' },
  { order_id: 5196, order_number: 'ORD-2026-005196', order_date: '2026-11-12 08:30:15', customer_name: 'Summit Biometrics Ltd', customer_segment: 'Enterprise', product_summary: 'FIPS 140-3 Hardware Security Module', gross_revenue: 5400.00, discount_amount: 0.00, refund_amount: 5400.00, net_amount: 0.00, status: 'Refunded', payment_method: 'Wire Transfer' },
  { order_id: 5195, order_number: 'ORD-2026-005195', order_date: '2026-11-11 16:22:50', customer_name: 'Borealis Media Network', customer_segment: 'Mid-Market', product_summary: 'Predictive Churn Engine Subscription', gross_revenue: 4200.00, discount_amount: 630.00, refund_amount: 0.00, net_amount: 3570.00, status: 'Completed', payment_method: 'Credit Card' },
  { order_id: 5194, order_number: 'ORD-2026-005194', order_date: '2026-11-11 10:14:05', customer_name: 'Quantum Edge Labs', customer_segment: 'Enterprise', product_summary: 'Enterprise Virtual Private Cloud', gross_revenue: 4400.00, discount_amount: 880.00, refund_amount: 0.00, net_amount: 3520.00, status: 'Completed', payment_method: 'Wire Transfer' },
  { order_id: 5193, order_number: 'ORD-2026-005193', order_date: '2026-11-10 15:45:33', customer_name: 'Crestline Aerospace Group', customer_segment: 'Enterprise', product_summary: 'Cloud Migration Sprint (40 Hours)', gross_revenue: 6000.00, discount_amount: 0.00, refund_amount: 0.00, net_amount: 6000.00, status: 'Completed', payment_method: 'Wire Transfer' }
];

export const MOCK_BUSINESS_INSIGHTS = [
  {
    id: 'ins-rev-growth',
    type: 'success',
    title: 'Positive Revenue Velocity',
    description: 'Net realized revenue expanded by 15.0% compared to the prior period, reaching $24,980,392.55.',
    metric_value: '+15.0%',
    recommendation: 'Maintain inventory depth for leading stock keeping units to prevent stock-outs during demand peaks.',
    category: 'Revenue'
  },
  {
    id: 'ins-margin-healthy',
    type: 'success',
    title: 'Strong Margin Protection',
    description: 'Gross margin performance is resilient at 37.2%, sustaining solid net unit economics.',
    metric_value: '37.2% Margin',
    recommendation: 'Reinvest surplus operating cash flows into customer acquisition and top-tier product lines.',
    category: 'Profitability'
  },
  {
    id: 'ins-prod-margin-14',
    type: 'warning',
    title: 'High Volume / Thin Margin Alert: FIPS 140-3 HSM',
    description: "Product 'FIPS 140-3 Hardware Security Module' generated $1,432,000.00 in sales but delivers an underperforming profit margin of only 17.0% (Discount rate: 6.0%).",
    metric_value: '17.0% margin',
    recommendation: 'Calibrate pricing structure or establish a maximum coupon discount ceiling for PRD-HW-02.',
    category: 'Product'
  },
  {
    id: 'ins-cat-concentration-1',
    type: 'info',
    title: 'Category Concentration: Cloud & Infrastructure',
    description: "'Cloud & Infrastructure' represents 33.9% of aggregate enterprise revenue ($8,465,000.00).",
    metric_value: '33.9% of Total',
    recommendation: 'Diversify marketing spend across secondary categories to reduce revenue reliance on a single segment.',
    category: 'Revenue'
  },
  {
    id: 'ins-reg-top-1',
    type: 'info',
    title: 'Dominant Regional Hub: North America - East',
    description: 'North America - East leads territorial performance with $6,985,000.00 in sales and a healthy 37.5% profit margin.',
    metric_value: '$6,985,000.00',
    recommendation: 'Scale regional marketing campaigns in NA-EAST while examining under-indexing in LATAM.',
    category: 'Regional'
  },
  {
    id: 'ins-refund-driver',
    type: 'warning',
    title: 'Primary Refund Driver: Defective Item',
    description: "'Defective Item' accounts for 34.2% of all refund claims ($266,472.00).",
    metric_value: '34.2% of Refunds',
    recommendation: "Coordinate with logistics and QA engineering to remediate causes tied to 'Defective Item'.",
    category: 'Refund'
  }
];

