/**
 * RevenueGuard Centralized API Service Layer
 * Connects frontend modules directly to live FastAPI backend endpoints.
 * Handles JWT access tokens, automatic silent refresh, and RBAC authorization headers.
 */

const BASE_URL = (import.meta.env.VITE_API_URL || '/api').replace(/\/+$/, '');

let isRefreshing = false;
let refreshSubscribers = [];

function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

export function getStoredAccessToken() {
  try {
    return localStorage.getItem('rg_access_token');
  } catch {
    return null;
  }
}

export function getStoredRefreshToken() {
  try {
    return localStorage.getItem('rg_refresh_token');
  } catch {
    return null;
  }
}

export function setStoredTokens(accessToken, refreshToken) {
  try {
    if (accessToken) localStorage.setItem('rg_access_token', accessToken);
    if (refreshToken) localStorage.setItem('rg_refresh_token', refreshToken);
  } catch (e) {
    console.warn('Storage write failed:', e);
  }
}

export function clearStoredTokens() {
  try {
    localStorage.removeItem('rg_access_token');
    localStorage.removeItem('rg_refresh_token');
  } catch (e) {
    console.warn('Storage removal failed:', e);
  }
}

/**
 * Builds a clean query string from an object of parameters.
 * Normalizes date presets ('all' -> 2020-01-01, '12m' -> default backend trailing 12 months).
 */
function buildQueryString(params = {}) {
  const query = new URLSearchParams();

  if (params.datePreset === 'all' && !params.start_date) {
    query.append('start_date', '2020-01-01');
  } else if (params.start_date) {
    query.append('start_date', params.start_date);
  }

  if (params.end_date) {
    query.append('end_date', params.end_date);
  }

  if (params.category_id !== undefined && params.category_id !== null && params.category_id !== '') {
    query.append('category_id', params.category_id);
  }

  if (params.region_id !== undefined && params.region_id !== null && params.region_id !== '') {
    query.append('region_id', params.region_id);
  }

  if (params.limit !== undefined && params.limit !== null) {
    query.append('limit', params.limit);
  }

  if (params.offset !== undefined && params.offset !== null) {
    query.append('offset', params.offset);
  }

  if (params.search) {
    query.append('search', params.search);
  }

  if (params.grain) {
    query.append('grain', params.grain);
  }

  if (params.min_pct !== undefined && params.min_pct !== null) {
    query.append('min_pct', params.min_pct);
  }

  if (params.threshold_pct !== undefined && params.threshold_pct !== null) {
    query.append('threshold_pct', params.threshold_pct);
  }

  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

/**
 * Centralized fetch wrapper with timeout, JSON parsing, auth header injection,
 * automatic token rotation on 401, and unified error handling.
 */
async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeout || 30000);

  const token = getStoredAccessToken();
  const defaultHeaders = {
    Accept: 'application/json',
    ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers: defaultHeaders,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Silent refresh on 401 for authenticated sessions
    if (
      response.status === 401 &&
      !options._retry &&
      !endpoint.startsWith('/auth/login') &&
      !endpoint.startsWith('/auth/refresh')
    ) {
      const refreshToken = getStoredRefreshToken();
      if (refreshToken) {
        if (!isRefreshing) {
          isRefreshing = true;
          try {
            const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (refreshRes.ok) {
              const newTokens = await refreshRes.json();
              setStoredTokens(newTokens.access_token, newTokens.refresh_token);
              isRefreshing = false;
              onRefreshed(newTokens.access_token);
              return request(endpoint, { ...options, _retry: true });
            } else {
              clearStoredTokens();
              isRefreshing = false;
              onRefreshed(null);
              window.dispatchEvent(new CustomEvent('rg:auth:expired'));
            }
          } catch {
            clearStoredTokens();
            isRefreshing = false;
            onRefreshed(null);
            window.dispatchEvent(new CustomEvent('rg:auth:expired'));
          }
        } else {
          return new Promise((resolve, reject) => {
            subscribeTokenRefresh((newToken) => {
              if (newToken) {
                resolve(request(endpoint, { ...options, _retry: true }));
              } else {
                const err = new Error('Session expired');
                err.status = 401;
                reject(err);
              }
            });
          });
        }
      }
    }

    // Parse response
    const contentType = response.headers.get('content-type') || '';
    let data = null;
    if (contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      const errorMessage =
        (data && typeof data === 'object' && (data.detail || data.message)) ||
        (typeof data === 'string' && data) ||
        `HTTP Error ${response.status}: ${response.statusText}`;
      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error(`API request to ${endpoint} timed out after 30 seconds.`);
    }
    if (err.status) {
      throw err;
    }
    throw new Error(err.message || 'Unable to connect to RevenueGuard backend service.');
  }
}

// HTTP Helper verbs
const get = (endpoint, params = {}) => request(`${endpoint}${buildQueryString(params)}`, { method: 'GET' });
const post = (endpoint, body = {}) =>
  request(endpoint, {
    method: 'POST',
    body: body instanceof FormData ? body : JSON.stringify(body),
  });

/**
 * Downloads a file directly from a streaming backend endpoint.
 */
async function downloadFile(endpoint, defaultFilename = 'export.csv', params = {}) {
  const token = getStoredAccessToken();
  const url = `${BASE_URL}${endpoint}${buildQueryString(params)}`;
  const response = await fetch(url, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (!response.ok) {
    throw new Error(`Failed to download report: ${response.statusText}`);
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;

  const disposition = response.headers.get('content-disposition');
  let filename = defaultFilename;
  if (disposition && disposition.includes('filename=')) {
    filename = disposition.split('filename=')[1].replace(/["']/g, '').trim();
  }

  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

/**
 * Centralized API client exporting all service methods.
 */
export const api = {
  // Authentication & RBAC
  login: (email, password) => post('/auth/login', { email, password }),
  logout: (refreshToken) => post('/auth/logout', { refresh_token: refreshToken }),
  refresh: (refreshToken) => post('/auth/refresh', { refresh_token: refreshToken }),
  getMe: () => get('/auth/me'),
  getPermissions: () => get('/auth/permissions'),
  changePassword: (currentPassword, newPassword) =>
    post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
  getUsers: () => get('/auth/users'),
  createUser: (userData) => post('/auth/users', userData),
  updateUserStatus: (userId, isActive) =>
    request(`/auth/users/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: isActive }),
    }),
  updateUserRole: (userId, role) =>
    request(`/auth/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    }),

  // Filters & Lookups
  getFilters: (params) => get('/overview/filters', params),

  // 1. Overview Module
  getKPIs: (params) => get('/overview/kpis', params),
  getTrends: (params) => get('/overview/trends', params),
  getCategoryBreakdown: (params) => get('/overview/category-breakdown', params),
  getTopProducts: (params) => get('/overview/top-products', params),
  getRegionalSales: (params) => get('/overview/regional-sales', params),
  getRecentTransactions: (params) => get('/overview/recent-transactions', params),
  getInsights: (params) => get('/overview/insights', params),

  // 2. Revenue Analytics Module
  getRevenueSummary: (params) => get('/revenue/summary', params),
  getRevenueTrends: (params) => get('/revenue/trends', params),
  getRevenueByCategory: (params) => get('/revenue/by-category', params),
  getRevenueByRegion: (params) => get('/revenue/by-region', params),
  getRevenueByProduct: (params) => get('/revenue/by-product', params),

  // 3. Sales Performance Module
  getSalesSummary: (params) => get('/sales/summary', params),
  getSalesByPayment: (params) => get('/sales/payment-methods', params),
  getSalesTransactions: (params) => get('/sales/transactions', params),

  // 4. Discount Analysis Module
  getDiscountSummary: (params) => get('/discounts/summary', params),
  getDiscountsByType: (params) => get('/discounts/by-type', params),
  getDiscountsByCategory: (params) => get('/discounts/by-category', params),
  getHighDiscountOrders: (params) => get('/discounts/high-discount-orders', params),

  // 5. Refund Analysis Module
  getRefundSummary: (params) => get('/refunds/summary', params),
  getRefundReasons: (params) => get('/refunds/reasons', params),
  getRefundsByCategory: (params) => get('/refunds/by-category', params),
  getHighRefundProducts: (params) => get('/refunds/high-refund-products', params),

  // 6. Profitability Analysis Module
  getProfitSummary: (params) => get('/profitability/summary', params),
  getProfitTrends: (params) => get('/profitability/monthly-trends', params),
  getProductQuadrant: (params) => get('/profitability/product-quadrant', params),

  // 7. Product Insights Module
  getProductPerformance: (params) => get('/products/performance', params),
  getBestSellers: (params) => get('/products/best-sellers', params),
  getLowPerformers: (params) => get('/products/low-performers', params),

  // 8. Customer Insights Module
  getCustomerSummary: (params) => get('/customers/summary', params),
  getCustomerSegments: (params) => get('/customers/segmentation', params),
  getTopCustomers: (params) => get('/customers/top-customers', params),

  // 9. Regional Analysis Module
  getRegionalPerformance: (params) => get('/regional/performance', params),

  // 10. Reports & Exports Module
  getExecutiveReport: (params) => get('/reports/summary', params),
  exportTransactionsCSV: (params) =>
    downloadFile('/reports/export/transactions/csv', 'revenueguard_transactions.csv', params),
  exportTransactionsExcel: (params) =>
    downloadFile('/reports/export/transactions/excel', 'revenueguard_full_bi_report.xlsx', params),
  getPowerBIDataset: (params) => get('/reports/power-bi/dataset', params),

  // 11. Data Management Module
  validateDataset: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return post('/data/validate', formData);
  },
  uploadDataset: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return post('/data/upload', formData);
  },
  getUploadHistory: () => get('/data/history'),
  reseedData: () => post('/data/reseed-sample-data?confirm=true', {}),
  executeSQL: (query) => post('/data/execute-sql', { query }),
  healthCheck: () => get('/health'),
};

export default api;
