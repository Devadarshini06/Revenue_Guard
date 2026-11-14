import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/layout/Sidebar';
import Navbar from './components/layout/Navbar';
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
import { api } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [filterOptions, setFilterOptions] = useState(null);

  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    category_id: undefined,
    region_id: undefined,
    search: '',
    datePreset: 'all'
  });

  // Load global filter bounds and categories
  useEffect(() => {
    api.getFilters()
      .then((opts) => setFilterOptions(opts))
      .catch((err) => console.error('Failed to load filter options:', err));
  }, []);

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    // Trigger re-render by creating a new filter object reference
    setFilters(prev => ({ ...prev, _timestamp: Date.now() }));
    setTimeout(() => setIsRefreshing(false), 800);
  }, []);

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
    <div className="min-h-screen bg-[#FAF9F6] flex">
      {/* 1. Left Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        {/* 2. Top Navigation Bar */}
        <Navbar
          filters={filters}
          setFilters={setFilters}
          filterOptions={filterOptions}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          setIsMobileOpen={setIsMobileOpen}
        />

        {/* 3. Page Content Wrapper */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {renderActivePage()}
        </main>
      </div>
    </div>
  );
}

