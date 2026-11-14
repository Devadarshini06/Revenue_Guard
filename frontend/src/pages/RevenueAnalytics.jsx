import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { TrendingUp, DollarSign, ArrowUpRight, ArrowDownRight, Layers, Globe, Filter } from 'lucide-react';
import { api } from '../services/api';
import ChartCard from '../components/common/ChartCard';
import KPICard from '../components/common/KPICard';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function RevenueAnalytics({ filters }) {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState([]);
  const [categories, setCategories] = useState([]);
  const [regional, setRegional] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [timeGrain, setTimeGrain] = useState('monthly'); // monthly, quarterly
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getRevenueSummary(filters),
      api.getRevenueTrends(filters),
      api.getRevenueByCategory(filters),
      api.getRevenueByRegion(filters),
      api.getRevenueByProduct({ ...filters, limit: 12 })
    ])
      .then(([sumData, trendData, catData, regData, prodData]) => {
        if (!isMounted) return;
        setSummary(sumData);
        setTrends(trendData || []);
        setCategories(catData || []);
        setRegional(regData || []);
        setTopProducts(prodData || []);
      })
      .catch((err) => console.error('Revenue analytics load error:', err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [filters]);

  if (loading && !summary) {
    return <LoadingSpinner text="Running multi-period revenue calculations..." />;
  }

  // Quarterly aggregated trends from monthly data
  const quarterlyTrends = React.useMemo(() => {
    const quarters = {};
    trends.forEach((t) => {
      const parts = t.date.split('-');
      const year = parts[0];
      const month = parseInt(parts[1], 10);
      const q = Math.ceil(month / 3);
      const key = `${year} Q${q}`;

      if (!quarters[key]) {
        quarters[key] = {
          date: key,
          label: key,
          gross_revenue: 0,
          net_revenue: 0,
          profit: 0,
          discounts: 0,
          refunds: 0
        };
      }
      quarters[key].gross_revenue += t.gross_revenue;
      quarters[key].net_revenue += t.net_revenue;
      quarters[key].profit += t.profit;
      quarters[key].discounts += t.discounts;
      quarters[key].refunds += t.refunds;
    });
    return Object.values(quarters);
  }, [trends]);

  const displayTrends = timeGrain === 'quarterly' ? quarterlyTrends : trends;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-brand-dark">
            Detailed Revenue Analytics
          </h1>
          <p className="text-xs text-brand-gray mt-0.5">
            Gross vs net revenue progression, growth velocities, and period comparisons.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="bg-background border border-border rounded-lg p-1 flex items-center text-xs">
            <button
              onClick={() => setTimeGrain('monthly')}
              className={`px-3 py-1 rounded font-medium transition-colors ${
                timeGrain === 'monthly' ? 'bg-card text-brand-dark shadow-2xs font-semibold' : 'text-brand-gray hover:text-brand-dark'
              }`}
            >
              Monthly Grain
            </button>
            <button
              onClick={() => setTimeGrain('quarterly')}
              className={`px-3 py-1 rounded font-medium transition-colors ${
                timeGrain === 'quarterly' ? 'bg-card text-brand-dark shadow-2xs font-semibold' : 'text-brand-gray hover:text-brand-dark'
              }`}
            >
              Quarterly Grain
            </button>
          </div>
        </div>
      </div>

      {/* Summary KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Gross Bookings" kpi={summary?.gross_revenue} icon={DollarSign} />
        <KPICard title="Net Realized Revenue" kpi={summary?.net_revenue} icon={TrendingUp} />
        <KPICard title="Promotional Discounts" kpi={summary?.discounts} icon={Layers} />
        <KPICard title="Refund Leakage" kpi={summary?.refunds} icon={Globe} />
      </div>

      {/* Main Revenue Trajectory & Growth Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard
          title="Revenue Trajectory & Net Realization"
          subtitle="Tracking gross billing, discounts, refunds, and final net recognized revenue"
          className="lg:col-span-2"
          height="h-80"
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={displayTrends} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <defs>
                <linearGradient id="netRevArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#C5A880" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#C5A880" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="label" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, '']} />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Area type="monotone" dataKey="net_revenue" name="Net Realized Revenue" stroke="#C5A880" strokeWidth={2.5} fill="url(#netRevArea)" />
              <Line type="monotone" dataKey="gross_revenue" name="Gross Bookings" stroke="#231F1D" strokeWidth={2} dot={false} strokeDasharray="4 4" />
              <Line type="monotone" dataKey="profit" name="Gross Profit" stroke="#8C6E46" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Growth Velocity Column */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-brand-dark tracking-tight mb-1">
              Period Growth Velocity
            </h3>
            <p className="text-xs text-brand-gray mb-4">
              Window function (LAG) period-over-period percentage growth.
            </p>

            <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
              {trends.slice().reverse().map((t, idx) => (
                <div key={t.date} className="flex items-center justify-between text-xs p-2 rounded-lg bg-background border border-border/60">
                  <div>
                    <span className="font-semibold text-brand-dark">{t.label}</span>
                    <div className="text-[10px] text-brand-gray">${t.net_revenue.toLocaleString()} net</div>
                  </div>

                  <div className="flex items-center gap-1">
                    <span className={`font-mono font-bold text-xs ${
                      t.growth_rate > 0 ? 'text-emerald-700' : t.growth_rate < 0 ? 'text-rose-700' : 'text-gray-500'
                    }`}>
                      {t.growth_rate > 0 ? `+${t.growth_rate}%` : `${t.growth_rate}%`}
                    </span>
                    {t.growth_rate > 0 ? (
                      <ArrowUpRight size={14} className="text-emerald-600" />
                    ) : t.growth_rate < 0 ? (
                      <ArrowDownRight size={14} className="text-rose-600" />
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Revenue by Product & Revenue by Region */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Revenue by Product Catalog"
          subtitle="Top generating products with unit volume"
          height="h-80"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topProducts} layout="vertical" margin={{ top: 5, right: 20, left: 50, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" horizontal={false} />
              <XAxis type="number" stroke="#A09891" fontSize={11} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <YAxis type="category" dataKey="sku" stroke="#231F1D" fontSize={11} tickLine={false} />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Net Revenue']} />
              <Bar dataKey="revenue" name="Net Revenue" fill="#231F1D" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Regional Revenue Performance"
          subtitle="Geographic territory distribution"
          height="h-80"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={regional} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="code" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Revenue']} />
              <Bar dataKey="revenue" name="Revenue" fill="#C5A880" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

