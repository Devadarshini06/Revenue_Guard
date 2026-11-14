import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { RotateCcw, AlertOctagon, TrendingDown, ShieldAlert } from 'lucide-react';
import { api } from '../api';
import ChartCard from '../components/common/ChartCard';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';

const REASON_COLORS = ['#231F1D', '#8C6E46', '#C5A880', '#D7C1A3', '#68625D'];

export default function RefundAnalysis({ filters }) {
  const [summary, setSummary] = useState(null);
  const [reasons, setReasons] = useState([]);
  const [categoryRefunds, setCategoryRefunds] = useState([]);
  const [highRefundProducts, setHighRefundProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getRefundSummary(filters),
      api.getRefundReasons(filters),
      api.getRefundsByCategory(filters),
      api.getHighRefundProducts({ limit: 20 })
    ])
      .then(([sumData, resData, catData, highData]) => {
        if (!isMounted) return;
        setSummary(sumData);
        setReasons(resData || []);
        setCategoryRefunds(catData || []);
        setHighRefundProducts(highData || []);
      })
      .catch((err) => console.error('Refund analysis load error:', err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [filters]);

  if (loading && !summary) {
    return <LoadingSpinner text="Auditing customer return patterns and leakage..." />;
  }

  const highRefundColumns = [
    { key: 'sku', header: 'SKU', render: (v) => <span className="font-mono font-medium">{v}</span> },
    { key: 'product_name', header: 'Product Name', render: (v) => <span className="font-medium text-brand-dark">{v}</span> },
    { key: 'category_name', header: 'Category' },
    { key: 'refund_claims', header: 'Claims', align: 'center', render: (v) => <span className="font-mono">{v}</span> },
    { key: 'gross_sales', header: 'Gross Sales', align: 'right', render: (v) => `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
    { key: 'total_refunded', header: 'Total Refunded', align: 'right', render: (v) => (
      <span className="font-semibold text-rose-700">-${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
    )},
    { key: 'refund_rate', header: 'Refund Rate %', align: 'center', render: (v) => (
      <span className={`px-2 py-0.5 rounded font-mono font-bold text-xs ${
        v >= 6.0 ? 'bg-rose-100 text-rose-800 border border-rose-300' : 'bg-amber-50 text-amber-800'
      }`}>
        {v}%
      </span>
    )}
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-brand-dark">
          Refund Analytics & Revenue Leakage Audit
        </h1>
        <p className="text-xs text-brand-gray mt-0.5">
          Identify post-sale return volume, root causes, defect patterns, and product quality issues.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Total Refund Capital</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-rose-700"><RotateCcw size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">${summary?.total_refund_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className="text-[11px] text-brand-gray">Total refunded customer settlements</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Portfolio Refund Rate</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-amber-700"><TrendingDown size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">{summary?.refund_rate}%</div>
          <div className="text-[11px] text-brand-gray">Refund capital vs gross billing value</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Refunded Orders Count</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-brand-dark"><AlertOctagon size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">{summary?.refunded_orders_count.toLocaleString()}</div>
          <div className="text-[11px] text-brand-gray">Orders with full or partial refunds</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Quality Leakage Risk</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-rose-700"><ShieldAlert size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">
            {summary?.refund_rate > 5.0 ? 'ELEVATED' : 'CONTROLLED'}
          </div>
          <div className="text-[11px] text-brand-gray">Automated QA threshold assessment</div>
        </div>
      </div>

      {/* Visualizations: Reasons Breakdown & Refunds by Category */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Root Cause Breakdown (Refund Reasons)"
          subtitle="Proportion of clawbacks attributable to specific return reasons"
          height="h-72"
        >
          <div className="flex flex-col h-full">
            <div className="h-44">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={reasons}
                    dataKey="total_amount"
                    nameKey="reason"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={65}
                    paddingAngle={3}
                  >
                    {reasons.map((entry, index) => (
                      <Cell key={`res-${index}`} fill={REASON_COLORS[index % REASON_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Total Amount']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-1 overflow-y-auto max-h-24">
              {reasons.map((r, i) => (
                <div key={r.reason} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: REASON_COLORS[i % REASON_COLORS.length] }}></span>
                    <span className="text-brand-dark">{r.reason}</span>
                  </div>
                  <span className="font-mono text-brand-gray">{r.percentage}% (${Number(r.total_amount).toLocaleString()})</span>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>

        <ChartCard
          title="Refund Capital by Category"
          subtitle="Clawback volume across divisions"
          height="h-72"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={categoryRefunds} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="category_name" stroke="#A09891" fontSize={10} tickLine={false} interval={0} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Total Refunded']} />
              <Bar dataKey="refund_amount" name="Refund Amount" fill="#8C6E46" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* High-Refund Products Table */}
      <DataTable
        title="Elevated Return Products (Revenue Leakage Watchlist)"
        subtitle="Catalog items exhibiting abnormal defect rates or return frequencies"
        columns={highRefundColumns}
        data={highRefundProducts}
        pageSize={8}
      />
    </div>
  );
}

