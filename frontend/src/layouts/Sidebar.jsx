import React from 'react';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  TrendingUp,
  BarChart3,
  Percent,
  RotateCcw,
  Scale,
  Package,
  Users,
  Globe2,
  FileSpreadsheet,
  Database,
  Settings as SettingsIcon,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

export const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'revenue', label: 'Revenue Analytics', icon: TrendingUp },
  { id: 'sales', label: 'Sales Performance', icon: BarChart3 },
  { id: 'discounts', label: 'Discount Analysis', icon: Percent },
  { id: 'refunds', label: 'Refund Analysis', icon: RotateCcw },
  { id: 'profitability', label: 'Profitability Analysis', icon: Scale },
  { id: 'products', label: 'Product Insights', icon: Package },
  { id: 'customers', label: 'Customer Insights', icon: Users },
  { id: 'regional', label: 'Regional Analysis', icon: Globe2 },
  { id: 'reports', label: 'Reports & Exports', icon: FileSpreadsheet },
  { id: 'data', label: 'Data Management', icon: Database },
  { id: 'settings', label: 'Settings', icon: SettingsIcon },
];

export default function Sidebar({ activeTab, setActiveTab, isMobileOpen, setIsMobileOpen }) {
  const { user, hasPermission } = useAuth();

  const filteredNavItems = NAV_ITEMS.filter((item) => {
    if (item.id === 'data') {
      return hasPermission('manage:data') || hasPermission('execute:sql');
    }
    if (item.id === 'settings') {
      return user?.role === 'Super Admin' || user?.role === 'Admin';
    }
    return true;
  });
  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-xs"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#231F1D] text-[#E5E1DD] flex flex-col border-r border-[#332D2A] transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-[#332D2A]">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#C5A880] to-[#8C6E46] flex items-center justify-center text-[#231F1D] shadow-md">
            <ShieldCheck size={20} strokeWidth={2.5} />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-base tracking-tight text-white">RevenueGuard</span>
              <span className="text-[9px] font-mono font-semibold uppercase px-1.5 py-0.5 rounded bg-[#C5A880]/20 text-[#C5A880] border border-[#C5A880]/30">PRO</span>
            </div>
            <p className="text-[11px] text-[#A09891] leading-none">Financial Intelligence</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-[#A09891]/80">
            Platform Modules
          </div>

          {filteredNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  if (setIsMobileOpen) setIsMobileOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all group ${
                  isActive
                    ? 'bg-[#3A3431] text-[#C5A880] shadow-xs'
                    : 'text-[#E5E1DD]/80 hover:bg-[#2F2A28] hover:text-white'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    size={17}
                    className={`shrink-0 transition-colors ${
                      isActive ? 'text-[#C5A880]' : 'text-[#A09891] group-hover:text-white'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>

                {isActive && (
                  <div className="w-1.5 h-1.5 rounded-full bg-[#C5A880] shadow-[0_0_8px_#C5A880]" />
                )}
              </button>
            );
          })}
        </nav>

        {/* System & Data Status Footer */}
        <div className="p-4 border-t border-[#332D2A] bg-[#1E1A18]/60">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-[11px] font-medium text-[#E5E1DD]">Live Database Active</span>
            </div>
            <span className="text-[10px] font-mono text-emerald-400 uppercase">Connected</span>
          </div>
          <div className="text-[10px] text-[#A09891] leading-relaxed">
            Connected to FastAPI analytical engine & SQLite database.
          </div>
        </div>
      </aside>
    </>
  );
}

