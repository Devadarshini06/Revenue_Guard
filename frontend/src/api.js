const BASE_URL = '/api';

function buildQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value);
    }
  });
  const str = query.toString();
  return str ? `?${str}` : '';
}

async function request(endpoint, options = {}) {
  try {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Accept': 'application/json',
        ...options.headers,
      },
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Request failed with status ${res.status}`);
    }

    return await res.json();
  } catch (error) {
    console.error(`API Error on ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // Overview
  getFilters: () => request('/overview/filters'),
  getKPIs: (params) => request(`/overview/kpis${buildQuery(params)}`),
  getTrends: (params) => request(`/overview/trends${buildQuery(params)}`),
  getCategoryBreakdown: (params) => request(`/overview/category-breakdown${buildQuery(params)}`),
  getTopProducts: (params) => request(`/overview/top-products${buildQuery(params)}`),
  getRegionalSales: (params) => request(`/overview/regional-sales${buildQuery(params)}`),
  getRecentTransactions: (params) => request(`/overview/recent-transactions${buildQuery(params)}`),
  getInsights: (params) => request(`/overview/insights${buildQuery(params)}`),

  // Revenue Analytics
  getRevenueSummary: (params) => request(`/revenue/summary${buildQuery(params)}`),
  getRevenueTrends: (params) => request(`/revenue/trends${buildQuery(params)}`),
  getRevenueByCategory: (params) => request(`/revenue/by-category${buildQuery(params)}`),
  getRevenueByRegion: (params) => request(`/revenue/by-region${buildQuery(params)}`),
  getRevenueByProduct: (params) => request(`/revenue/by-product${buildQuery(params)}`),

  // Sales Performance
  getSalesSummary: (params) => request(`/sales/summary${buildQuery(params)}`),
  getSalesByPayment: (params) => request(`/sales/payment-methods${buildQuery(params)}`),
  getSalesTransactions: (params) => request(`/sales/transactions${buildQuery(params)}`),

  // Discount Analysis
  getDiscountSummary: (params) => request(`/discounts/summary${buildQuery(params)}`),
  getDiscountsByType: (params) => request(`/discounts/by-type${buildQuery(params)}`),
  getDiscountsByCategory: (params) => request(`/discounts/by-category${buildQuery(params)}`),
  getHighDiscountOrders: (params) => request(`/discounts/high-discount-orders${buildQuery(params)}`),

  // Refund Analysis
  getRefundSummary: (params) => request(`/refunds/summary${buildQuery(params)}`),
  getRefundReasons: (params) => request(`/refunds/reasons${buildQuery(params)}`),
  getRefundsByCategory: (params) => request(`/refunds/by-category${buildQuery(params)}`),
  getHighRefundProducts: (params) => request(`/refunds/high-refund-products${buildQuery(params)}`),

  // Profitability Analysis
  getProfitSummary: (params) => request(`/profitability/summary${buildQuery(params)}`),
  getProfitTrends: (params) => request(`/profitability/monthly-trends${buildQuery(params)}`),
  getProductQuadrant: (params) => request(`/profitability/product-quadrant${buildQuery(params)}`),

  // Product Insights
  getProductPerformance: (params) => request(`/products/performance${buildQuery(params)}`),
  getBestSellers: (params) => request(`/products/best-sellers${buildQuery(params)}`),
  getLowPerformers: (params) => request(`/products/low-performers${buildQuery(params)}`),

  // Customer Insights
  getCustomerSummary: (params) => request(`/customers/summary${buildQuery(params)}`),
  getCustomerSegments: (params) => request(`/customers/segmentation${buildQuery(params)}`),
  getTopCustomers: (params) => request(`/customers/top-customers${buildQuery(params)}`),

  // Regional Analysis
  getRegionalPerformance: (params) => request(`/regional/performance${buildQuery(params)}`),

  // Reports
  getExecutiveReport: (params) => request(`/reports/summary${buildQuery(params)}`),
  getPowerBIDataset: () => request('/reports/power-bi/dataset'),

  // Data Management
  validateDataset: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${BASE_URL}/data/validate`, {
      method: 'POST',
      body: formData,
    }).then(res => res.json());
  },
  uploadDataset: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${BASE_URL}/data/upload`, {
      method: 'POST',
      body: formData,
    }).then(res => res.json());
  },
  getUploadHistory: () => request('/data/history'),
  reseedData: () => request('/data/reseed-sample-data', { method: 'POST' }),
  executeSQL: (query) => request('/data/execute-sql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  }),
};

