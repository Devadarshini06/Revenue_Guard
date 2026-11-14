import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { Percent, AlertTriangle, TrendingDown, Tag } from 'lucide-react';
import { api } from '../api';
import ChartCard from '../components/common/ChartCard';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function DiscountAnalysis({ filters }) {
  const [summary, setSummary] = useState(null);
  const [discountTypes, setDiscountTypes] = useState([]);
  const [categoryDiscounts, setCategoryDiscounts] = useState([]);
  const [highDiscountOrders, setHighDiscountOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getDiscountSummary(filters),
      api.getDiscountsByType(filters),
      api.getDiscountsByCategory(filters),
      api.getHighDiscountOrders({ min_pct: 15.0, limit: 50 })
    ])
      .then(([sumData, typeData, catData, highData]) => {
        if (!isMounted) return;
        setSummary(sumData);
        setDiscountTypes(typeData || []);
        setCategoryDiscounts(catData || []);
        setHighDiscountOrders(highData || []);
      })
      .catch((err) => console.error('Discount analysis load error:', err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [filters]);

  if (loading && !summary) {
    return <LoadingSpinner text="Computing promotional discount erosion models..." />;
  }

  const highDiscountColumns = [
    { key: 'order_number', header: 'Order Ref', render: (v) => <span className="font-mono font-medium">{v}</span> },
    { key: 'customer_name', header: 'Customer' },
    { key: 'product_name', header: 'Product' },
    { key: 'reason', header: 'Campaign / Reason', render: (v) => <span className="text-[11px] text-brand-gray italic">{v}</span> },
    { key: 'gross_revenue', header: 'Gross Value', align: 'right', render: (v) => `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
    { key: 'discount_percentage', header: 'Discount %', align: 'center', render: (v) => (
      <span className="px-2 py-0.5 rounded font-mono font-semibold bg-rose-50 text-rose-700 border border-rose-200 text-[11px]">
        {v}%
      </span>
    )},
    { key: 'discount_amount', header: 'Discount Concession', align: 'right', render: (v) => (
      <span className="font-semibold text-rose-700">-${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
    )},
    { key: 'profit', header: 'Net Profit', align: 'right', render: (v) => `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-brand-dark">
          Promotional Discount & Margin Erosion Analytics
        </h1>
        <p className="text-xs text-brand-gray mt-0.5">
          Evaluate coupon usage, volume tier concessions, and revenue reduction across catalogs.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Total Discounts</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-amber-700"><Percent size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">${summary?.total_discounts.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className="text-[11px] text-brand-gray">Total promotional dollars subtracted</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Average Concession</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-bronze"><Tag size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">{summary?.average_discount_percentage}%</div>
          <div className="text-[11px] text-brand-gray">Mean discount rate across eligible orders</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Gross Revenue Erosion</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-rose-700"><TrendingDown size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">{summary?.revenue_erosion_rate}%</div>
          <div className="text-[11px] text-brand-gray">Proportion of gross bookings eroded</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Discount Instances</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-brand-dark"><AlertTriangle size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">{summary?.total_instances.toLocaleString()}</div>
          <div className="text-[11px] text-brand-gray">Orders utilizing coupon or volume pricing</div>
        </div>
      </div>

      {/* Visualizations: Discount by Category & Discount by Code */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Discount Concessions by Category"
          subtitle="Total dollars conceded across catalog divisions"
          height="h-72"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={categoryDiscounts} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="category_name" stroke="#A09891" fontSize={10} tickLine={false} interval={0} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Discounts Conceded']} />
              <Bar dataKey="discount_amount" name="Discounts" fill="#C5A880" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Revenue Before vs After Discounts"
          subtitle="Impact of active discount codes on top revenue streams"
          height="h-72"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={discountTypes} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="discount_code" stroke="#A09891" fontSize={10} tickLine={false} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, '']} />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Bar dataKey="revenue_before" name="Gross Bookings" fill="#231F1D" radius={[4, 4, 0, 0]} />
              <Bar dataKey="revenue_after" name="Net Realized" fill="#C5A880" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* High-Discount Transactions Table */}
      <DataTable
        title="High-Discount Transactions Audit (≥15% Concession)"
        subtitle="Individual orders where significant discount rates impacted unit profitability"
        columns={highDiscountColumns}
        data={highDiscountOrders}
        pageSize={8}
      />
    </div>
  );
}

