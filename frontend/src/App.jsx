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
import Login from './pages/Login';
import { useFilters } from './hooks/useFilters';
import { api } from './services/api';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ShieldCheck } from 'lucide-react';

function RevenueGuardApp() {
  const { user, isLoading, hasPermission } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [filterOptions, setFilterOptions] = useState(null);
  const { filters, setFilters } = useFilters();

  // Load global filter bounds and categories from backend API when authenticated
  useEffect(() => {
    if (!user) return;
    api
      .getFilters()
      .then((opts) => setFilterOptions(opts))
      .catch((err) => console.error('Failed to load filter options:', err));
  }, [user]);

  // Adjust active tab if user role restricts access
  useEffect(() => {
    if (!user) return;
    if (activeTab === 'data' && !hasPermission('manage:data') && !hasPermission('execute:sql')) {
      setActiveTab('overview');
    } else if (activeTab === 'settings' && user.role !== 'Super Admin' && user.role !== 'Admin') {
      setActiveTab('overview');
    }
  }, [user, activeTab, hasPermission]);

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    setFilters((prev) => ({ ...prev, _timestamp: Date.now() }));
    setTimeout(() => setIsRefreshing(false), 500);
  }, [setFilters]);

  // Splash Loading Screen
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#231F1D] flex flex-col items-center justify-center text-white">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#C5A880] to-[#8C6E46] flex items-center justify-center text-[#231F1D] shadow-xl mb-4 border border-[#E5E1DD]/20 animate-pulse">
          <ShieldCheck size={32} strokeWidth={2.2} />
        </div>
        <div className="text-sm font-semibold tracking-wider text-[#E5E1DD] flex items-center gap-2">
          <span>INITIALIZING REVENUEGUARD</span>
        </div>
        <div className="w-32 h-1 bg-[#3A3431] rounded-full mt-3 overflow-hidden">
          <div className="w-1/2 h-full bg-[#C5A880] rounded-full animate-[shimmer_1.5s_infinite]" />
        </div>
      </div>
    );
  }

  // Unauthenticated -> Render Login
  if (!user) {
    return <Login />;
  }

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

export default function App() {
  return (
    <AuthProvider>
      <RevenueGuardApp />
    </AuthProvider>
  );
}
