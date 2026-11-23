import React, { useState } from 'react';
import {
  Menu,
  Calendar,
  RefreshCw,
  Bell,
  Search,
  User,
  CheckCircle2,
  AlertCircle,
  Filter,
  X
} from 'lucide-react';

export default function Navbar({
  filters,
  setFilters,
  filterOptions,
  onRefresh,
  isRefreshing,
  setIsMobileOpen
}) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);

  const notifications = [
    {
      id: 1,
      title: 'Monthly Analytics Model Updated',
      desc: 'All 5,200 transactions recalculated with updated margin metrics.',
      time: 'Just now',
      type: 'info'
    },
    {
      id: 2,
      title: 'Refund Spike Alert: PRD-DAT-03',
      desc: 'Predictive Churn Engine reported 3 refund requests this week.',
      time: '1 hour ago',
      type: 'warning'
    },
    {
      id: 3,
      title: 'High-Discount Approved',
      desc: 'Order ORD-2026-004819 approved with Volume Discount (-20%).',
      time: '3 hours ago',
      type: 'success'
    }
  ];

  const handleDatePreset = (preset) => {
    const today = new Date();
    let start = new Date();

    if (preset === '30d') {
      start.setDate(today.getDate() - 30);
    } else if (preset === '90d') {
      start.setDate(today.getDate() - 90);
    } else if (preset === '12m') {
      setFilters(prev => ({ ...prev, start_date: '', end_date: '', datePreset: '12m' }));
      setShowDatePicker(false);
      return;
    } else if (preset === 'all') {
      setFilters(prev => ({ ...prev, start_date: '', end_date: '', datePreset: 'all' }));
      setShowDatePicker(false);
      return;
    }

    setFilters(prev => ({
      ...prev,
      start_date: start.toISOString().split('T')[0],
      end_date: today.toISOString().split('T')[0],
      datePreset: preset
    }));
    setShowDatePicker(false);
  };

  return (
    <header className="h-16 bg-card border-b border-border sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6">
      {/* Left: Mobile Toggle & Search */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <button
          onClick={() => setIsMobileOpen(true)}
          className="lg:hidden p-2 text-brand-gray hover:text-brand-dark rounded-lg hover:bg-background"
        >
          <Menu size={20} />
        </button>

        <div className="relative w-full max-w-xs hidden sm:block">
          <Search size={15} className="absolute left-3 top-2.5 text-brand-gray" />
          <input
            type="text"
            placeholder="Search orders, products, SKUs, customers..."
            value={filters.search || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze focus:bg-white transition-all placeholder:text-brand-gray/60"
          />
          {filters.search && (
            <button
              onClick={() => setFilters(prev => ({ ...prev, search: '' }))}
              className="absolute right-2.5 top-2.5 text-brand-gray hover:text-brand-dark"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Right: Date Range, Filters, Sync Badge, Notifications, Profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Date Filter Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowDatePicker(!showDatePicker)}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-background hover:bg-[#FAF9F6] border border-border rounded-lg text-brand-dark transition-colors shadow-2xs"
          >
            <Calendar size={14} className="text-bronze" />
            <span className="hidden sm:inline">
              {filters.datePreset === '30d'
                ? 'Past 30 Days'
                : filters.datePreset === '90d'
                ? 'Past 90 Days'
                : filters.datePreset === '12m'
                ? 'Trailing 12 Months (Default)'
                : filters.datePreset === 'all'
                ? 'All Time Data (18 Months)'
                : filters.start_date
                ? `${filters.start_date} ~ ${filters.end_date || 'Now'}`
                : 'Trailing 12 Months (Default)'}
            </span>
            <span className="sm:hidden">Date</span>
          </button>

          {showDatePicker && (
            <div className="absolute right-0 mt-2 w-72 bg-card border border-border rounded-xl shadow-elevated p-3 z-50">
              <div className="text-xs font-semibold text-brand-dark mb-2">Select Date Period</div>
              <div className="grid grid-cols-2 gap-1.5 mb-3">
                <button
                  onClick={() => handleDatePreset('12m')}
                  className={`px-2.5 py-1.5 text-xs rounded-md text-left font-medium transition-colors ${
                    filters.datePreset === '12m' ? 'bg-bronze text-white' : 'hover:bg-background text-brand-gray'
                  }`}
                >
                  Trailing 12M (Default)
                </button>
                <button
                  onClick={() => handleDatePreset('all')}
                  className={`px-2.5 py-1.5 text-xs rounded-md text-left font-medium transition-colors ${
                    filters.datePreset === 'all' ? 'bg-bronze text-white' : 'hover:bg-background text-brand-gray'
                  }`}
                >
                  All Time (18 Months)
                </button>
                <button
                  onClick={() => handleDatePreset('30d')}
                  className={`px-2.5 py-1.5 text-xs rounded-md text-left font-medium transition-colors ${
                    filters.datePreset === '30d' ? 'bg-bronze text-white' : 'hover:bg-background text-brand-gray'
                  }`}
                >
                  Past 30 Days
                </button>
                <button
                  onClick={() => handleDatePreset('90d')}
                  className={`px-2.5 py-1.5 text-xs rounded-md text-left font-medium transition-colors ${
                    filters.datePreset === '90d' ? 'bg-bronze text-white' : 'hover:bg-background text-brand-gray'
                  }`}
                >
                  Past 90 Days
                </button>
              </div>

              <div className="border-t border-border pt-2.5">
                <div className="text-[11px] font-medium text-brand-gray mb-1.5">Custom Date Range</div>
                <div className="space-y-1.5">
                  <input
                    type="date"
                    value={filters.start_date || ''}
                    onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value, datePreset: 'custom' }))}
                    className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
                  />
                  <input
                    type="date"
                    value={filters.end_date || ''}
                    onChange={(e) => setFilters(prev => ({ ...prev, end_date: e.target.value, datePreset: 'custom' }))}
                    className="w-full px-2 py-1 text-xs border border-border rounded bg-background"
                  />
                </div>
              </div>

              <div className="mt-2.5 flex justify-end">
                <button
                  onClick={() => setShowDatePicker(false)}
                  className="px-3 py-1 bg-brand-dark text-white text-xs rounded font-medium hover:bg-black"
                >
                  Apply
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Global Category / Region Selector */}
        {filterOptions && filterOptions.categories && (
          <select
            value={filters.category_id || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, category_id: e.target.value || undefined }))}
            className="hidden md:block px-2.5 py-1.5 text-xs bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
          >
            <option value="">All Categories</option>
            {filterOptions.categories.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        )}

        {/* Refresh Action */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh analytical engine"
          className="p-2 text-brand-gray hover:text-brand-dark rounded-lg hover:bg-background border border-border transition-colors"
        >
          <RefreshCw size={14} className={isRefreshing ? 'animate-spin text-bronze' : ''} />
        </button>

        {/* Data Sync Status Pill */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200/60 text-[11px] font-medium text-emerald-800">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
          <span>Live Sync</span>
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 text-brand-gray hover:text-brand-dark rounded-lg hover:bg-background border border-border transition-colors relative"
          >
            <Bell size={14} />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-bronze" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-card border border-border rounded-xl shadow-elevated p-3 z-50">
              <div className="flex items-center justify-between pb-2 border-b border-border">
                <span className="text-xs font-semibold text-brand-dark">Platform Notifications</span>
                <span className="text-[10px] font-mono text-bronze uppercase">3 new</span>
              </div>
              <div className="divide-y divide-border/60 max-h-64 overflow-y-auto">
                {notifications.map(n => (
                  <div key={n.id} className="py-2.5">
                    <div className="text-xs font-medium text-brand-dark">{n.title}</div>
                    <div className="text-[11px] text-brand-gray mt-0.5 leading-tight">{n.desc}</div>
                    <div className="text-[10px] text-brand-gray/80 mt-1">{n.time}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Profile */}
        <div className="flex items-center gap-2 pl-1 border-l border-border/80">
          <div className="w-8 h-8 rounded-full bg-bronze/20 border border-bronze/40 flex items-center justify-center text-bronze-dark font-bold text-xs">
            JD
          </div>
          <div className="hidden xl:block text-left leading-tight">
            <div className="text-xs font-semibold text-brand-dark">Julia Davies</div>
            <div className="text-[10px] text-brand-gray">VP Revenue Ops</div>
          </div>
        </div>
      </div>
    </header>
  );
}

