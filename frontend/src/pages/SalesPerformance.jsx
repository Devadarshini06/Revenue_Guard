import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { ShoppingBag, Box, CreditCard, DollarSign, Wallet } from 'lucide-react';
import { api } from '../services/api';
import ChartCard from '../components/common/ChartCard';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';

const PAYMENT_COLORS = ['#231F1D', '#C5A880', '#8C6E46', '#68625D'];

export default function SalesPerformance({ filters }) {
  const [summary, setSummary] = useState(null);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [trends, setTrends] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getSalesSummary(filters),
      api.getSalesByPayment(filters),
      api.getRevenueTrends(filters),
      api.getSalesTransactions({ limit: 100 })
    ])
      .then(([sumData, payData, trendData, txnData]) => {
        if (!isMounted) return;
        setSummary(sumData);
        setPaymentMethods(payData || []);
        setTrends(trendData || []);
        setTransactions(txnData || []);
      })
      .catch((err) => console.error('Sales performance load error:', err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [filters]);

  if (loading && !summary) {
    return <LoadingSpinner text="Analyzing sales execution and volumes..." />;
  }

  const columns = [
    { key: 'order_number', header: 'Order Ref', render: (v) => <span className="font-mono font-medium">{v}</span> },
    { key: 'order_date', header: 'Date', render: (v) => v.split(' ')[0] },
    { key: 'customer_name', header: 'Customer' },
    { key: 'customer_segment', header: 'Segment', render: (v) => <span className="text-[10px] px-2 py-0.5 rounded bg-background border border-border">{v}</span> },
    { key: 'payment_method', header: 'Payment Method', render: (v) => <span className="font-medium text-brand-dark">{v}</span> },
    { key: 'gross_revenue', header: 'Gross', align: 'right', render: (v) => `$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
    { key: 'discount_amount', header: 'Discount', align: 'right', render: (v) => `-$${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
    { key: 'net_amount', header: 'Net Settled', align: 'right', render: (v) => <span className="font-semibold">${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span> },
    { key: 'status', header: 'Status', align: 'center', render: (v) => (
      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
        v === 'Completed' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
      }`}>
        {v}
      </span>
    )}
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-brand-dark">
          Sales Performance & Order Velocity
        </h1>
        <p className="text-xs text-brand-gray mt-0.5">
          Order volumes, units moved, average order value, payment channels, and transactions.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Total Orders Booked</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-bronze"><ShoppingBag size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">{summary?.total_orders.toLocaleString()}</div>
          <div className="text-[11px] text-brand-gray">Commercial transactions completed</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Units Moved</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-bronze"><Box size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">{summary?.total_units_sold.toLocaleString()}</div>
          <div className="text-[11px] text-brand-gray">Individual catalog units fulfilled</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Average Order Value</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-bronze"><DollarSign size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">${summary?.average_order_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className="text-[11px] text-brand-gray">Mean net revenue per transaction</div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">Total Booked Sales</span>
            <div className="p-2 bg-background border border-border/60 rounded-lg text-bronze"><CreditCard size={16} /></div>
          </div>
          <div className="text-2xl font-bold text-brand-dark mb-1">${summary?.total_sales.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div className="text-[11px] text-brand-gray">Net transaction revenue pool</div>
        </div>
      </div>

      {/* Charts: Sales Trends & Payment Methods */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard
          title="Monthly Order Volume Progression"
          subtitle="Count of distinct commercial purchase orders per month"
          className="lg:col-span-2"
          height="h-72"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={trends} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="label" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis stroke="#A09891" fontSize={11} tickLine={false} />
              <Tooltip />
              <Bar dataKey="orders_count" name="Orders Count" fill="#231F1D" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Sales by Payment Method"
          subtitle="Volume split by settlement rail"
          className="lg:col-span-1"
          height="h-72"
        >
          <div className="flex flex-col h-full">
            <div className="h-44">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={paymentMethods}
                    dataKey="total_amount"
                    nameKey="payment_method"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={65}
                    paddingAngle={3}
                  >
                    {paymentMethods.map((entry, index) => (
                      <Cell key={`pay-${index}`} fill={PAYMENT_COLORS[index % PAYMENT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Total Sales']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-1 overflow-y-auto max-h-24">
              {paymentMethods.map((p, i) => (
                <div key={p.payment_method} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PAYMENT_COLORS[i % PAYMENT_COLORS.length] }}></span>
                    <span className="text-brand-dark">{p.payment_method}</span>
                  </div>
                  <span className="font-mono text-brand-gray">${Number(p.total_amount).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>
      </div>

      {/* Sortable & Searchable Sales Transactions Table */}
      <DataTable
        title="Commercial Sales Transactions Ledger"
        subtitle="Sortable and searchable record of individual customer sales"
        columns={columns}
        data={transactions}
        pageSize={12}
      />
    </div>
  );
}

