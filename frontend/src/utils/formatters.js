/**
 * Formatting utilities for RevenueGuard frontend
 */

export function formatCurrency(value, currency = 'USD') {
  if (value === null || value === undefined) return '$0.00';
  const symbols = {
    USD: '$',
    EUR: '€',
    GBP: '£'
  };
  const sym = symbols[currency] || '$';
  return `${sym}${Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

export function formatNumber(value) {
  if (value === null || value === undefined) return '0';
  return Number(value).toLocaleString();
}

export function formatPercent(value, decimals = 1) {
  if (value === null || value === undefined) return '0.0%';
  return `${Number(value).toFixed(decimals)}%`;
}

export function formatDate(dateString) {
  if (!dateString) return '—';
  const parts = dateString.split(' ')[0].split('-');
  if (parts.length === 3) {
    return `${parts[0]}-${parts[1]}-${parts[2]}`;
  }
  return dateString;
}
