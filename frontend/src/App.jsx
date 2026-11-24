import React, { useState, useEffect, useCallback } from 'react';
import MainLayout from './layouts/MainLayout';
import Overview from './pages/Overview';
import RevenueAnalytics from './pages/RevenueAnalytics';
import SalesPerformance from './pages/SalesPerformance';
import DiscountAnalysis from './pages/DiscountAnalysis';
import RefundAnalysis from './pages/RefundAnalysis';
import ProfitabilityAnalysis from './pages/ProfitabilityAnalysis';
import ProductInsights from './pages/ProductInsights';
import CustomerInsights from './pages/CustomerInsights';
import RegionalAnalysis from './pages/RegionalAnalysis';
import ReportsExports from './pages/ReportsExports';
import DataManagement from './pages/DataManagement';
import Settings from './pages/Settings';
import { useFilters } from './hooks/useFilters';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [filterOptions, setFilterOptions] = useState(null);
  const { filters, setFilters } = useFilters();

  // Load global filter bounds and categories from backend API
  useEffect(() => {
    api.getFilters()
      .then((opts) => setFilterOptions(opts))
      .catch((err) => console.error('Failed to load filter options:', err));
  }, []);

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    setFilters(prev => ({ ...prev, _timestamp: Date.now() }));
    setTimeout(() => setIsRefreshing(false), 500);
  }, [setFilters]);

  const renderActivePage = () => {
    switch (activeTab) {
      case 'overview':
        return <Overview filters={filters} onNavigate={setActiveTab} />;
      case 'revenue':
        return <RevenueAnalytics filters={filters} />;
      case 'sales':
        return <SalesPerformance filters={filters} />;
      case 'discounts':
        return <DiscountAnalysis filters={filters} />;
      case 'refunds':
        return <RefundAnalysis filters={filters} />;
      case 'profitability':
        return <ProfitabilityAnalysis filters={filters} />;
      case 'products':
        return <ProductInsights filters={filters} />;
      case 'customers':
        return <CustomerInsights filters={filters} />;
      case 'regional':
        return <RegionalAnalysis filters={filters} />;
      case 'reports':
        return <ReportsExports filters={filters} />;
      case 'data':
        return <DataManagement />;
      case 'settings':
        return <Settings />;
      default:
        return <Overview filters={filters} onNavigate={setActiveTab} />;
    }
  };

  return (
    <MainLayout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      filters={filters}
      setFilters={setFilters}
      filterOptions={filterOptions}
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
    >
      {renderActivePage()}
    </MainLayout>
  );
}
