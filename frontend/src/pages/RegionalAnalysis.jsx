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
import { Globe2, MapPin, Building2, TrendingUp, AlertCircle } from 'lucide-react';
import { api } from '../api';
import ChartCard from '../components/common/ChartCard';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function RegionalAnalysis({ filters }) {
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    api.getRegionalPerformance(filters)
      .then((data) => {
        if (!isMounted) return;
        setRegions(data || []);
      })
      .catch((err) => console.error('Regional analysis error:', err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [filters]);

  if (loading && regions.length === 0) {
    return <LoadingSpinner text="Mapping multi-territorial operations..." />;
  }

  const columns = [
    { key: 'code', header: 'Region Code', render: (v) => <span className="font-mono font-bold text-xs">{v}</span> },
    { key: 'region_name', header: 'Territory Name', render: (v, r) => (
      <div>
        <div className="font-semibold text-brand-dark">{v}</div>
        <div className="text-[10px] text-brand-gray">{r.city ? `${r.city}, ${r.country}` : r.country}</div>
      </div>
    )},
    { key: 'orders_count', header: 'Orders', align: 'center', render: (v) => v.toLocaleString() },
    { key: 'gross_revenue', header: 'Gross Value', align: 'right', render: (v) => `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
    { key: 'discount_amount', header: 'Discounts', align: 'right', render: (v) => `-$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
    { key: 'refund_amount', header: 'Refunds', align: 'right', render: (v) => `-$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
    { key: 'revenue', header: 'Net Realized', align: 'right', render: (v) => (
      <span className="font-semibold text-brand-dark">${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
    )},
    { key: 'profit', header: 'Profit Yield', align: 'right', render: (v) => (
      <span className="font-medium text-emerald-700">${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
    )},
    { key: 'profit_margin', header: 'Margin %', align: 'center', render: (v) => (
      <span className="px-2 py-0.5 rounded font-mono font-bold text-xs bg-background border border-border">
        {v}%
      </span>
    )},
    { key: 'refund_rate', header: 'Refund Rate', align: 'center', render: (v) => (
      <span className={`font-mono ${v >= 5 ? 'text-rose-700 font-semibold' : 'text-brand-gray'}`}>{v}%</span>
    )}
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-brand-dark">
          Geographic & Regional Performance Analytics
        </h1>
        <p className="text-xs text-brand-gray mt-0.5">
          Territorial performance comparisons across Americas, EMEA, and Asia-Pacific hubs.
        </p>
      </div>

      {/* Regional Comparison Visual Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {regions.slice(0, 4).map((r) => (
          <div key={r.region_id} className="bg-card border border-border rounded-xl p-5 shadow-subtle hover:shadow-card transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-background border border-border text-brand-dark">
                {r.code}
              </span>
              <span className="text-xs font-semibold text-emerald-700">{r.profit_margin}% margin</span>
            </div>
            <div className="font-bold text-sm text-brand-dark truncate">{r.region_name}</div>
            <div className="text-[11px] text-brand-gray mb-3">{r.city}, {r.country}</div>

            <div className="pt-3 border-t border-border flex items-center justify-between text-xs">
              <span className="text-brand-gray">Net Revenue:</span>
              <span className="font-semibold text-brand-dark">${Number(r.revenue).toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Visualizations: Comparative Regional Bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Revenue & Gross Profit by Territory"
          subtitle="Top line vs retained margin across operating regions"
          height="h-72"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={regions} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="code" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, '']} />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Bar dataKey="revenue" name="Net Revenue" fill="#231F1D" radius={[4, 4, 0, 0]} />
              <Bar dataKey="profit" name="Gross Profit" fill="#C5A880" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Discount and Refund Ratios by Region"
          subtitle="Assessing territorial concession levels and clawback risks"
          height="h-72"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={regions} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="code" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} tickFormatter={(v) => `${v}%`} />
              <Tooltip formatter={(val) => [`${val}%`, '']} />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Bar dataKey="discount_rate" name="Discount Rate %" fill="#8C6E46" radius={[4, 4, 0, 0]} />
              <Bar dataKey="refund_rate" name="Refund Rate %" fill="#D7C1A3" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Main Regional DataTable */}
      <DataTable
        title="Territorial Operations Performance Ledger"
        subtitle="Complete regional breakdown of commercial volume, margins, and deductions"
        columns={columns}
        data={regions}
        pageSize={8}
      />
    </div>
  );
}

