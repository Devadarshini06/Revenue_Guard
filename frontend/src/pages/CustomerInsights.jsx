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
import { Users, UserCheck, Repeat, DollarSign, Building } from 'lucide-react';
import { api } from '../services/api';
import ChartCard from '../components/common/ChartCard';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';

const SEGMENT_COLORS = ['#231F1D', '#C5A880', '#8C6E46', '#68625D'];

export default function CustomerInsights({ filters }) {
  const [summary, setSummary] = useState(null);
  const [segments, setSegments] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getCustomerSummary(filters),
      api.getCustomerSegments(filters),
      api.getTopCustomers({ limit: 50 })
    ])
      .then(([sumData, segData, topData]) => {
        if (!isMounted) return;
        setSummary(sumData);
        setSegments(segData || []);
        setTopCustomers(topData || []);
      })
      .catch((err) => console.error('Customer insights error:', err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [filters]);

  if (loading && !summary) {
    return <LoadingSpinner text="Segmenting customer cohorts and spend metrics..." />;
  }

  const customerColumns = [
    { key: 'customer_code', header: 'Account Code', render: (v) => <span className="font-mono text-bronze-dark font-medium">{v}</span> },
    { key: 'name', header: 'Account / Organization', render: (v) => <span className="font-semibold text-brand-dark">{v}</span> },
    { key: 'segment', header: 'Segment', render: (v) => (
      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-background border border-border">
        {v}
      </span>
    )},
    { key: 'region_name', header: 'Region' },
    { key: 'email', header: 'Contact', render: (v) => <span className="text-[11px] text-brand-gray">{v}</span> },
    { key: 'total_orders', header: 'Orders Count', align: 'center', render: (v) => <span className="font-mono">{v}</span> },
    { key: 'total_spent', header: 'Total Net Revenue', align: 'right', render: (v) => (
      <span className="font-semibold text-brand-dark">${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
    )},
    { key: 'refund_total', header: 'Refund Claims', align: 'right', render: (v) => (
      <span className={v > 0 ? 'text-rose-700 font-medium' : 'text-brand-gray'}>
        {v > 0 ? `-$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '$0.00'}
      </span>
    )}
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-brand-dark">
          Customer Insights & Cohort Segmentation
        </h1>
        <p className="text-xs text-brand-gray mt-0.5">
          Account lifetime value, cohort segmentation (Enterprise, Mid-Market, SMB), and repeat frequencies.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Total Customer Base</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-bronze"><Users size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">{summary?.total_customers.toLocaleString()}</div>
          <div className="text-[11px] text-brand-gray">Registered commercial accounts</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Average Account Spend</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-emerald-700"><DollarSign size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">${summary?.average_customer_spending.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className="text-[11px] text-brand-gray">Mean revenue yield per client</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Active Contract Orders</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-brand-dark"><UserCheck size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">{summary?.active_orders.toLocaleString()}</div>
          <div className="text-[11px] text-brand-gray">Orders executed in current filter scope</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Account Repeat Rate</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-bronze"><Repeat size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">94.8%</div>
          <div className="text-[11px] text-brand-gray">Multi-order enterprise retention</div>
        </div>
      </div>

      {/* Visualizations: Segment Distribution & Revenue by Segment */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Revenue Contribution by Customer Segment"
          subtitle="Monetary split between Enterprise, Mid-Market, SMB, and Direct Consumer"
          height="h-72"
        >
          <div className="flex flex-col h-full">
            <div className="h-44">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={segments}
                    dataKey="revenue"
                    nameKey="segment"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={65}
                    paddingAngle={3}
                  >
                    {segments.map((entry, index) => (
                      <Cell key={`seg-${index}`} fill={SEGMENT_COLORS[index % SEGMENT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Revenue']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-1 overflow-y-auto max-h-24">
              {segments.map((s, i) => (
                <div key={s.segment} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: SEGMENT_COLORS[i % SEGMENT_COLORS.length] }}></span>
                    <span className="text-brand-dark">{s.segment}</span>
                  </div>
                  <span className="font-mono text-brand-gray">${Number(s.revenue).toLocaleString()} ({s.orders_count} orders)</span>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>

        <ChartCard
          title="Average Order Value by Segment"
          subtitle="Contract size differences across customer tiers"
          height="h-72"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={segments} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="segment" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v}`} />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, 'AOV']} />
              <Bar dataKey="average_order_value" name="Avg Order Value" fill="#C5A880" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Top Customers DataTable */}
      <DataTable
        title="Top Enterprise Accounts & Spending History"
        subtitle="Ranked clients ordered by aggregate net revenue contribution"
        columns={customerColumns}
        data={topCustomers}
        pageSize={10}
      />
    </div>
  );
}

