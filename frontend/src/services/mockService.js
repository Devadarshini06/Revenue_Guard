import {
  MOCK_FILTER_OPTIONS,
  MOCK_CATEGORIES,
  MOCK_REGIONS
} from '../mock-data/categoriesMock';

import {
  MOCK_KPIS,
  MOCK_TRENDS,
  MOCK_CATEGORIES_BREAKDOWN,
  MOCK_TOP_PRODUCTS,
  MOCK_REGIONAL_SALES,
  MOCK_RECENT_TRANSACTIONS,
  MOCK_BUSINESS_INSIGHTS
} from '../mock-data/overviewMock';

import {
  MOCK_SALES_SUMMARY,
  MOCK_PAYMENT_METHODS,
  MOCK_DISCOUNT_SUMMARY,
  MOCK_DISCOUNT_TYPES,
  MOCK_CATEGORY_DISCOUNTS,
  MOCK_HIGH_DISCOUNT_ORDERS,
  MOCK_REFUND_SUMMARY,
  MOCK_REFUND_REASONS,
  MOCK_HIGH_REFUND_PRODUCTS,
  MOCK_PROFIT_SUMMARY,
  MOCK_PRODUCT_QUADRANT,
  MOCK_CUSTOMER_SUMMARY,
  MOCK_CUSTOMER_SEGMENTS,
  MOCK_TOP_CUSTOMERS,
  MOCK_UPLOAD_HISTORY,
  MOCK_VALIDATION_SAMPLE
} from '../mock-data/specializedMock';

import { downloadCSV } from '../utils/exportUtils';

// Helper to simulate asynchronous execution delay for realistic UI responsiveness
const delay = (ms = 80) => new Promise((resolve) => setTimeout(resolve, ms));

export const mockService = {
  // Filters
  getFilters: async () => {
    await delay(30);
    return MOCK_FILTER_OPTIONS;
  },

  // Overview Module
  getKPIs: async (params = {}) => {
    await delay(60);
    // If a category filter is active, adjust values dynamically
    if (params.category_id) {
      const cat = MOCK_CATEGORIES_BREAKDOWN.find(c => c.category_id === Number(params.category_id));
      if (cat) {
        return {
          total_revenue: { ...MOCK_KPIS.total_revenue, formatted_value: `$${cat.gross_revenue.toLocaleString()}`, value: cat.gross_revenue },
          net_revenue: { ...MOCK_KPIS.net_revenue, formatted_value: `$${cat.revenue.toLocaleString()}`, value: cat.revenue },
          total_orders: { ...MOCK_KPIS.total_orders, formatted_value: cat.orders_count.toLocaleString(), value: cat.orders_count },
          average_order_value: { ...MOCK_KPIS.average_order_value, formatted_value: `$${(cat.revenue / cat.orders_count).toFixed(2)}`, value: cat.revenue / cat.orders_count },
          total_discounts: { ...MOCK_KPIS.total_discounts, formatted_value: `$${cat.discount_amount.toLocaleString()}`, value: cat.discount_amount },
          total_refunds: { ...MOCK_KPIS.total_refunds, formatted_value: `$${cat.refund_amount.toLocaleString()}`, value: cat.refund_amount },
          gross_profit: { ...MOCK_KPIS.gross_profit, formatted_value: `$${cat.profit.toLocaleString()}`, value: cat.profit },
          profit_margin: { ...MOCK_KPIS.profit_margin, formatted_value: `${cat.profit_margin}%`, value: cat.profit_margin }
        };
      }
    }
    return MOCK_KPIS;
  },

  getTrends: async (params = {}) => {
    await delay(60);
    return MOCK_TRENDS;
  },

  getCategoryBreakdown: async (params = {}) => {
    await delay(50);
    return MOCK_CATEGORIES_BREAKDOWN;
  },

  getTopProducts: async (params = {}) => {
    await delay(60);
    let list = [...MOCK_TOP_PRODUCTS];
    if (params.category_id) {
      const catObj = MOCK_CATEGORIES.find(c => c.id === Number(params.category_id));
      if (catObj) {
        list = list.filter(p => p.category_name.toLowerCase().includes(catObj.name.toLowerCase()));
      }
    }
    const limit = params.limit || 10;
    return list.slice(0, limit);
  },

  getRegionalSales: async (params = {}) => {
    await delay(50);
    return MOCK_REGIONAL_SALES;
  },

  getRecentTransactions: async (params = {}) => {
    await delay(70);
    let list = [...MOCK_RECENT_TRANSACTIONS];
    if (params.search) {
      const q = params.search.toLowerCase();
      list = list.filter(t =>
        t.order_number.toLowerCase().includes(q) ||
        t.customer_name.toLowerCase().includes(q) ||
        t.product_summary.toLowerCase().includes(q)
      );
    }
    const limit = params.limit || 50;
    return list.slice(0, limit);
  },

  getInsights: async (params = {}) => {
    await delay(50);
    return MOCK_BUSINESS_INSIGHTS;
  },

  // Revenue Analytics
  getRevenueSummary: async (params = {}) => {
    await delay(60);
    return {
      gross_revenue: MOCK_KPIS.total_revenue,
      net_revenue: MOCK_KPIS.net_revenue,
      discounts: MOCK_KPIS.total_discounts,
      refunds: MOCK_KPIS.total_refunds,
      growth_rate: 15.0
    };
  },

  getRevenueTrends: async (params = {}) => {
    await delay(60);
    return MOCK_TRENDS;
  },

  getRevenueByCategory: async (params = {}) => {
    await delay(50);
    return MOCK_CATEGORIES_BREAKDOWN;
  },

  getRevenueByRegion: async (params = {}) => {
    await delay(50);
    return MOCK_REGIONAL_SALES;
  },

  getRevenueByProduct: async (params = {}) => {
    await delay(60);
    return MOCK_TOP_PRODUCTS;
  },

  // Sales Performance
  getSalesSummary: async (params = {}) => {
    await delay(60);
    return MOCK_SALES_SUMMARY;
  },

  getSalesByPayment: async (params = {}) => {
    await delay(50);
    return MOCK_PAYMENT_METHODS;
  },

  getSalesTransactions: async (params = {}) => {
    await delay(70);
    let list = [...MOCK_RECENT_TRANSACTIONS];
    if (params.search) {
      const q = params.search.toLowerCase();
      list = list.filter(t =>
        t.order_number.toLowerCase().includes(q) ||
        t.customer_name.toLowerCase().includes(q) ||
        t.payment_method.toLowerCase().includes(q)
      );
    }
    return list;
  },

  // Discount Analysis
  getDiscountSummary: async (params = {}) => {
    await delay(60);
    return MOCK_DISCOUNT_SUMMARY;
  },

  getDiscountsByType: async (params = {}) => {
    await delay(50);
    return MOCK_DISCOUNT_TYPES;
  },

  getDiscountsByCategory: async (params = {}) => {
    await delay(50);
    return MOCK_CATEGORY_DISCOUNTS;
  },

  getHighDiscountOrders: async (params = {}) => {
    await delay(60);
    return MOCK_HIGH_DISCOUNT_ORDERS;
  },

  // Refund Analysis
  getRefundSummary: async (params = {}) => {
    await delay(60);
    return MOCK_REFUND_SUMMARY;
  },

  getRefundReasons: async (params = {}) => {
    await delay(50);
    return MOCK_REFUND_REASONS;
  },

  getRefundsByCategory: async (params = {}) => {
    await delay(50);
    return MOCK_CATEGORIES_BREAKDOWN.map(c => ({
      category_name: c.category_name,
      refund_amount: c.refund_amount,
      category_revenue: c.gross_revenue,
      refund_rate: Number(((c.refund_amount * 100) / c.gross_revenue).toFixed(2))
    }));
  },

  getHighRefundProducts: async (params = {}) => {
    await delay(60);
    return MOCK_HIGH_REFUND_PRODUCTS;
  },

  // Profitability Analysis
  getProfitSummary: async (params = {}) => {
    await delay(60);
    return MOCK_PROFIT_SUMMARY;
  },

  getProfitTrends: async (params = {}) => {
    await delay(60);
    return MOCK_TRENDS;
  },

  getProductQuadrant: async (params = {}) => {
    await delay(60);
    return MOCK_PRODUCT_QUADRANT;
  },

  // Product Insights
  getProductPerformance: async (params = {}) => {
    await delay(60);
    let list = [...MOCK_TOP_PRODUCTS];
    if (params.category_id) {
      const catObj = MOCK_CATEGORIES.find(c => c.id === Number(params.category_id));
      if (catObj) {
        list = list.filter(p => p.category_name.toLowerCase().includes(catObj.name.toLowerCase()));
      }
    }
    return list;
  },

  getBestSellers: async (params = {}) => {
    await delay(50);
    return MOCK_TOP_PRODUCTS.slice(0, 5);
  },

  getLowPerformers: async (params = {}) => {
    await delay(50);
    return [...MOCK_TOP_PRODUCTS].reverse().slice(0, 5);
  },

  // Customer Insights
  getCustomerSummary: async (params = {}) => {
    await delay(60);
    return MOCK_CUSTOMER_SUMMARY;
  },

  getCustomerSegments: async (params = {}) => {
    await delay(50);
    return MOCK_CUSTOMER_SEGMENTS;
  },

  getTopCustomers: async (params = {}) => {
    await delay(60);
    return MOCK_TOP_CUSTOMERS;
  },

  // Regional Analysis
  getRegionalPerformance: async (params = {}) => {
    await delay(60);
    return MOCK_REGIONAL_SALES;
  },

  // Reports & Exports
  getExecutiveReport: async (params = {}) => {
    await delay(120);
    return {
      kpis: MOCK_KPIS,
      categories: MOCK_CATEGORIES_BREAKDOWN,
      regions: MOCK_REGIONAL_SALES,
      trends: MOCK_TRENDS,
      generated_at: new Date().toISOString()
    };
  },

  exportTransactionsCSV: () => {
    downloadCSV('revenueguard_transactions_export.csv', MOCK_RECENT_TRANSACTIONS);
  },

  exportTransactionsExcel: () => {
    downloadCSV('revenueguard_full_bi_report.csv', MOCK_RECENT_TRANSACTIONS);
  },

  getPowerBIDataset: async () => {
    await delay(80);
    return MOCK_RECENT_TRANSACTIONS;
  },

  // Data Management
  validateDataset: async (file) => {
    await delay(250);
    if (!file) return MOCK_VALIDATION_SAMPLE;
    return {
      filename: file.name,
      total_rows: 320,
      valid_rows: 318,
      invalid_rows: 2,
      duplicate_rows: 0,
      missing_columns: [],
      missing_values: { discount_code: 35 },
      column_types: {
        order_number: 'object',
        order_date: 'datetime',
        customer_code: 'object',
        product_sku: 'object',
        quantity: 'int64',
        unit_price: 'float64',
        discount_amount: 'float64'
      },
      quality_score: 99.4,
      preview: MOCK_VALIDATION_SAMPLE.preview
    };
  },

  uploadDataset: async (file) => {
    await delay(300);
    return { success: true, message: 'Dataset uploaded and validated successfully.' };
  },

  getUploadHistory: async () => {
    await delay(50);
    return MOCK_UPLOAD_HISTORY;
  },

  reseedData: async () => {
    await delay(500);
    return { success: true, message: 'Database re-seeded with 5,200 sample orders.' };
  },

  executeSQL: async (query) => {
    await delay(200);
    const low = (query || '').toLowerCase();

    if (low.includes('monthly_rev') || low.includes('lag')) {
      return {
        columns: ['month', 'net_revenue', 'prev_month_revenue', 'growth_pct'],
        rows: MOCK_TRENDS.slice().reverse().map((t, idx, arr) => {
          const prev = arr[idx + 1] ? arr[idx + 1].net_revenue : t.net_revenue;
          return {
            month: t.date,
            net_revenue: t.net_revenue,
            prev_month_revenue: prev,
            growth_pct: t.growth_rate
          };
        }),
        row_count: MOCK_TRENDS.length
      };
    } else if (low.includes('category_summary') || low.includes('margin_percentage')) {
      return {
        columns: ['category', 'gross_sales', 'total_discounts', 'net_revenue', 'gross_profit', 'margin_percentage'],
        rows: MOCK_CATEGORIES_BREAKDOWN.map(c => ({
          category: c.category_name,
          gross_sales: c.gross_revenue,
          total_discounts: c.discount_amount,
          net_revenue: c.revenue,
          gross_profit: c.profit,
          margin_percentage: c.profit_margin
        })),
        row_count: MOCK_CATEGORIES_BREAKDOWN.length
      };
    } else if (low.includes('refund_reason')) {
      return {
        columns: ['refund_reason', 'claim_count', 'total_refunded', 'avg_claim_value'],
        rows: MOCK_REFUND_REASONS.map(r => ({
          refund_reason: r.reason,
          claim_count: r.count,
          total_refunded: r.total_amount,
          avg_claim_value: r.avg_amount
        })),
        row_count: MOCK_REFUND_REASONS.length
      };
    } else {
      // Default top products RANK query
      return {
        columns: ['sku', 'product_name', 'category_name', 'total_units_sold', 'net_revenue', 'gross_profit', 'revenue_rank'],
        rows: MOCK_TOP_PRODUCTS.map(p => ({
          sku: p.sku,
          product_name: p.name,
          category_name: p.category_name,
          total_units_sold: p.units_sold,
          net_revenue: p.revenue,
          gross_profit: p.profit,
          revenue_rank: p.rank
        })),
        row_count: MOCK_TOP_PRODUCTS.length
      };
    }
  }
};
