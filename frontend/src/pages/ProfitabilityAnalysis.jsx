import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ScatterChart,
  Scatter,
  ZAxis
} from 'recharts';
import { Scale, Percent, DollarSign, AlertCircle, ArrowUpRight } from 'lucide-react';
import { api } from '../services/api';
import ChartCard from '../components/common/ChartCard';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function ProfitabilityAnalysis({ filters }) {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState([]);
  const [quadrant, setQuadrant] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getProfitSummary(filters),
      api.getProfitTrends(filters),
      api.getProductQuadrant(filters)
    ])
      .then(([sumData, trendData, quadData]) => {
        if (!isMounted) return;
        setSummary(sumData);
        setTrends(trendData || []);
        setQuadrant(quadData || []);
      })
      .catch((err) => console.error('Profitability load error:', err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [filters]);

  if (loading && !summary) {
    return <LoadingSpinner text="Calculating gross margins and COGS allocations..." />;
  }

  const quadrantColumns = [
    { key: 'sku', header: 'SKU', render: (v) => <span className="font-mono font-medium">{v}</span> },
    { key: 'name', header: 'Product Name', render: (v) => <span className="font-medium text-brand-dark">{v}</span> },
    { key: 'category_name', header: 'Category' },
    { key: 'classification', header: 'Margin Matrix', render: (v) => {
      let colorClass = 'bg-gray-100 text-gray-800';
      if (v.includes('Star')) colorClass = 'bg-emerald-50 text-emerald-800 border border-emerald-200';
      else if (v.includes('Workhorse')) colorClass = 'bg-amber-50 text-amber-800 border border-amber-200';
      else if (v.includes('Niche')) colorClass = 'bg-blue-50 text-blue-800 border border-blue-200';
      else if (v.includes('Underperformer')) colorClass = 'bg-rose-50 text-rose-800 border border-rose-200';
      return <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${colorClass}`}>{v}</span>;
    }},
    { key: 'revenue', header: 'Net Revenue', align: 'right', render: (v) => `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
    { key: 'profit', header: 'Gross Profit', align: 'right', render: (v) => (
      <span className="font-semibold text-emerald-700">${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
    )},
    { key: 'profit_margin', header: 'Margin %', align: 'center', render: (v) => (
      <span className={`px-2 py-0.5 rounded font-mono font-bold text-xs ${
        v >= 45 ? 'text-emerald-700 bg-emerald-50' : v < 25 ? 'text-rose-700 bg-rose-50' : 'text-brand-dark'
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
          Profitability & Margin Integrity
        </h1>
        <p className="text-xs text-brand-gray mt-0.5">
          Unit economics, cost of goods sold (COGS), gross margin yields, and product profit matrix.
        </p>
      </div>

      {/* Summary KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Gross Profit</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-emerald-700"><Scale size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">${summary?.gross_profit.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className="text-[11px] text-brand-gray">Net revenue minus cost of goods sold</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Gross Profit Margin</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-bronze"><Percent size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">{summary?.profit_margin}%</div>
          <div className="text-[11px] text-brand-gray">Overall gross margin percentage yield</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Cost of Goods Sold (COGS)</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-brand-dark"><DollarSign size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">${summary?.cost_of_goods_sold.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className="text-[11px] text-brand-gray">Direct product unit acquisition costs</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Net Realized Revenue</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-bronze-dark"><Scale size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">${summary?.net_revenue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className="text-[11px] text-brand-gray">Top-line revenue base</div>
        </div>
      </div>

      {/* Visualizations: Revenue vs COGS & Monthly Profit Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Revenue vs Cost of Goods Sold (COGS)"
          subtitle="Direct comparison between top-line net sales and inventory procurement"
          height="h-72"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={trends} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="label" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, '']} />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Bar dataKey="net_revenue" name="Net Revenue" fill="#231F1D" radius={[4, 4, 0, 0]} />
              <Bar dataKey="profit" name="Profit Retained" fill="#C5A880" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Monthly Profit Progression"
          subtitle="Net monthly gross profit after refunds and procurement"
          height="h-72"
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trends} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="label" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Profit']} />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Line type="monotone" dataKey="profit" name="Gross Profit" stroke="#8C6E46" strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Product Profitability Matrix Table */}
      <DataTable
        title="Product Profitability & Margin Quadrant Matrix"
        subtitle="Catalog classification identifying high-volume/thin-margin risks vs star profit drivers"
        columns={quadrantColumns}
        data={quadrant}
        pageSize={8}
      />
    </div>
  );
}

