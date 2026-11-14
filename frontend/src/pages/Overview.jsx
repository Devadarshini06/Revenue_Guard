import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  TrendingUp,
  ShoppingCart,
  Receipt,
  Percent,
  RotateCcw,
  Scale,
  PercentSquare,
  ArrowUpRight,
  ChevronRight
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area
} from 'recharts';
import { api } from '../services/api';
import KPICard from '../components/common/KPICard';
import ChartCard from '../components/common/ChartCard';
import InsightBanner from '../components/common/InsightBanner';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';

const COLORS = ['#231F1D', '#C5A880', '#8C6E46', '#68625D', '#A09891', '#D7C1A3'];

export default function Overview({ filters, onNavigate }) {
  const [kpis, setKpis] = useState(null);
  const [trends, setTrends] = useState([]);
  const [categories, setCategories] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [regionalSales, setRegionalSales] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getKPIs(filters),
      api.getTrends(filters),
      api.getCategoryBreakdown(filters),
      api.getTopProducts({ ...filters, limit: 10 }),
      api.getRegionalSales(filters),
      api.getRecentTransactions({ limit: 15 }),
      api.getInsights(filters)
    ])
      .then(([kpiData, trendData, catData, prodData, regData, txnData, insData]) => {
        if (!isMounted) return;
        setKpis(kpiData);
        setTrends(trendData || []);
        setCategories(catData || []);
        setTopProducts(prodData || []);
        setRegionalSales(regData || []);
        setRecentTransactions(txnData || []);
        setInsights(insData || []);
      })
      .catch((err) => {
        console.error('Failed to load overview data:', err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [filters]);

  if (loading && !kpis) {
    return <LoadingSpinner text="Computing executive metrics from database..." />;
  }

  const transactionColumns = [
    {
      key: 'order_number',
      header: 'Order Ref',
      render: (val) => <span className="font-mono font-medium text-brand-dark">{val}</span>
    },
    {
      key: 'order_date',
      header: 'Date',
      render: (val) => <span className="text-brand-gray">{val.split(' ')[0]}</span>
    },
    {
      key: 'customer_name',
      header: 'Customer',
      render: (val, row) => (
        <div>
          <div className="font-medium text-brand-dark">{val}</div>
          <div className="text-[10px] text-brand-gray">{row.customer_segment}</div>
        </div>
      )
    },
    {
      key: 'product_summary',
      header: 'Products',
      render: (val) => (
        <span className="truncate max-w-[200px] block" title={val}>
          {val}
        </span>
      )
    },
    {
      key: 'gross_revenue',
      header: 'Gross Rev',
      align: 'right',
      render: (val) => `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
    },
    {
      key: 'discount_amount',
      header: 'Discount',
      align: 'right',
      render: (val) => (
        <span className={val > 0 ? 'text-amber-700' : 'text-brand-gray'}>
          {val > 0 ? `-$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '$0.00'}
        </span>
      )
    },
    {
      key: 'refund_amount',
      header: 'Refund',
      align: 'right',
      render: (val) => (
        <span className={val > 0 ? 'text-rose-700 font-medium' : 'text-brand-gray'}>
          {val > 0 ? `-$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '$0.00'}
        </span>
      )
    },
    {
      key: 'net_amount',
      header: 'Final Amount',
      align: 'right',
      render: (val) => (
        <span className="font-semibold text-brand-dark">
          ${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
      )
    },
    {
      key: 'status',
      header: 'Status',
      align: 'center',
      render: (val) => {
        const isCompleted = val === 'Completed';
        const isRefunded = val === 'Refunded';
        return (
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
              isCompleted
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : isRefunded
                ? 'bg-rose-50 text-rose-700 border border-rose-200'
                : 'bg-amber-50 text-amber-700 border border-amber-200'
            }`}
          >
            {val}
          </span>
        );
      }
    }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-brand-dark">
            Executive Revenue Overview
          </h1>
          <p className="text-xs text-brand-gray mt-0.5">
            Real-time financial analytics, volume trends, and margin health monitoring.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('reports')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-brand-dark text-white rounded-lg hover:bg-black transition-colors"
          >
            <span>Export BI Report</span>
            <ArrowUpRight size={14} />
          </button>
        </div>
      </div>

      {/* 8 Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Gross Revenue"
          kpi={kpis?.total_revenue}
          icon={DollarSign}
          loading={loading}
        />
        <KPICard
          title="Net Realized Revenue"
          kpi={kpis?.net_revenue}
          icon={TrendingUp}
          loading={loading}
        />
        <KPICard
          title="Total Orders"
          kpi={kpis?.total_orders}
          icon={ShoppingCart}
          loading={loading}
        />
        <KPICard
          title="Average Order Value (AOV)"
          kpi={kpis?.average_order_value}
          icon={Receipt}
          loading={loading}
        />
        <KPICard
          title="Total Discounts"
          kpi={kpis?.total_discounts}
          icon={Percent}
          loading={loading}
        />
        <KPICard
          title="Total Refunds"
          kpi={kpis?.total_refunds}
          icon={RotateCcw}
          loading={loading}
        />
        <KPICard
          title="Gross Profit"
          kpi={kpis?.gross_profit}
          icon={Scale}
          loading={loading}
        />
        <KPICard
          title="Profit Margin"
          kpi={kpis?.profit_margin}
          icon={PercentSquare}
          loading={loading}
        />
      </div>

      {/* Dynamic Business Insights Section */}
      <InsightBanner insights={insights} loading={loading} />

      {/* Visualizations Row 1: Revenue Trend & Revenue vs Profit */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Revenue Trend Line Chart */}
        <ChartCard
          title="1. Monthly Revenue Trend"
          subtitle="Gross book value vs net realized revenue after adjustments"
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trends} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <defs>
                <linearGradient id="grossGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#231F1D" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#231F1D" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="netGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#C5A880" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#C5A880" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="label" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis
                stroke="#A09891"
                fontSize={11}
                tickLine={false}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                formatter={(val) => [`$${Number(val).toLocaleString()}`, '']}
              />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Area
                type="monotone"
                dataKey="gross_revenue"
                name="Gross Revenue"
                stroke="#231F1D"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#grossGrad)"
              />
              <Area
                type="monotone"
                dataKey="net_revenue"
                name="Net Revenue"
                stroke="#C5A880"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#netGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* 2. Revenue vs Profit Comparative Chart */}
        <ChartCard
          title="2. Revenue vs Gross Profit"
          subtitle="Tracking unit economics and absolute profit yield over time"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={trends} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="label" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis
                stroke="#A09891"
                fontSize={11}
                tickLine={false}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, '']} />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Bar dataKey="net_revenue" name="Net Revenue" fill="#231F1D" radius={[4, 4, 0, 0]} />
              <Bar dataKey="profit" name="Gross Profit" fill="#C5A880" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Visualizations Row 2: Category Donut & Sales by Region */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 3. Revenue by Category (Donut Chart) */}
        <ChartCard
          title="3. Revenue by Category"
          subtitle="Portfolio distribution and concentration"
          className="lg:col-span-1"
        >
          <div className="flex flex-col h-full">
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categories}
                    dataKey="revenue"
                    nameKey="category_name"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                  >
                    {categories.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Revenue']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 space-y-1.5 overflow-y-auto max-h-24">
              {categories.map((c, i) => (
                <div key={c.category_id} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: COLORS[i % COLORS.length] }}
                    />
                    <span className="text-brand-dark truncate max-w-[130px]">{c.category_name}</span>
                  </div>
                  <span className="font-mono text-brand-gray">{c.percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>

        {/* 4. Sales by Region */}
        <ChartCard
          title="4. Sales by Region"
          subtitle="Territorial distribution across major international hubs"
          className="lg:col-span-2"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={regionalSales}
              layout="vertical"
              margin={{ top: 5, right: 20, left: 40, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" horizontal={false} />
              <XAxis
                type="number"
                stroke="#A09891"
                fontSize={11}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <YAxis
                type="category"
                dataKey="code"
                stroke="#231F1D"
                fontSize={11}
                tickLine={false}
              />
              <Tooltip
                formatter={(val, name) => [
                  `$${Number(val).toLocaleString()}`,
                  name === 'revenue' ? 'Net Revenue' : 'Profit'
                ]}
              />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Bar dataKey="revenue" name="Revenue" fill="#231F1D" radius={[0, 4, 4, 0]} />
              <Bar dataKey="profit" name="Profit" fill="#C5A880" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Visualizations Row 3: Top 10 Products & Discount vs Revenue */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 5. Top 10 Products (Horizontal Bar Chart) */}
        <ChartCard
          title="5. Top 10 Products"
          subtitle="Ranked by cumulative net revenue generation"
          height="h-80"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={topProducts}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" horizontal={false} />
              <XAxis
                type="number"
                stroke="#A09891"
                fontSize={11}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <YAxis
                type="category"
                dataKey="sku"
                stroke="#231F1D"
                fontSize={11}
                tickLine={false}
              />
              <Tooltip
                formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Revenue']}
                labelFormatter={(sku) => {
                  const prod = topProducts.find(p => p.sku === sku);
                  return prod ? `${prod.name} (${sku})` : sku;
                }}
              />
              <Bar dataKey="revenue" name="Net Revenue" fill="#C5A880" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* 6. Discount vs Revenue Comparative */}
        <ChartCard
          title="6. Discounts vs Net Revenue"
          subtitle="Monitoring monthly promotional concessions vs baseline revenue"
          height="h-80"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={trends} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F0ECE8" vertical={false} />
              <XAxis dataKey="label" stroke="#A09891" fontSize={11} tickLine={false} />
              <YAxis
                stroke="#A09891"
                fontSize={11}
                tickLine={false}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip formatter={(val) => [`$${Number(val).toLocaleString()}`, '']} />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Bar dataKey="net_revenue" name="Net Revenue" fill="#231F1D" radius={[4, 4, 0, 0]} />
              <Bar dataKey="discounts" name="Discounts Provided" fill="#D7C1A3" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* 7. Category Revenue Contribution Breakdown Table & Metrics */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-brand-dark tracking-tight">
              7. Category Revenue Contribution & Profit Margin Breakdown
            </h3>
            <p className="text-xs text-brand-gray mt-0.5">
              Comprehensive performance table with margin and orders statistics.
            </p>
          </div>
          <button
            onClick={() => onNavigate('products')}
            className="text-xs font-semibold text-bronze hover:text-bronze-dark flex items-center gap-1"
          >
            <span>View All Products</span>
            <ChevronRight size={14} />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-brand-dark">
            <thead className="bg-[#FAF9F6] border-b border-border text-[11px] uppercase tracking-wider text-brand-gray font-semibold">
              <tr>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3 text-right">Orders</th>
                <th className="px-4 py-3 text-right">Units Sold</th>
                <th className="px-4 py-3 text-right">Gross Revenue</th>
                <th className="px-4 py-3 text-right">Discounts</th>
                <th className="px-4 py-3 text-right">Refunds</th>
                <th className="px-4 py-3 text-right font-semibold">Net Revenue</th>
                <th className="px-4 py-3 text-right">Profit</th>
                <th className="px-4 py-3 text-right">Margin %</th>
                <th className="px-4 py-3 text-right">Share %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {categories.map((c) => (
                <tr key={c.category_id} className="hover:bg-background/80 transition-colors">
                  <td className="px-4 py-3 font-medium text-brand-dark">{c.category_name}</td>
                  <td className="px-4 py-3 text-right font-mono">{c.orders_count.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right font-mono">{c.units_sold.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right font-mono">${c.gross_revenue.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right font-mono text-amber-700">-${c.discount_amount.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right font-mono text-rose-700">-${c.refund_amount.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right font-mono font-semibold">${c.revenue.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right font-mono text-emerald-700">${c.profit.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right font-mono font-medium">{c.profit_margin}%</td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-bronze-dark">{c.percentage}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 8. Recent Transactions Table */}
      <DataTable
        title="Recent Transactions Audit Log"
        subtitle="Individual customer orders with gross, discount, refund, and net settlements"
        columns={transactionColumns}
        data={recentTransactions}
        pageSize={8}
        actions={
          <button
            onClick={() => onNavigate('sales')}
            className="text-xs font-semibold text-bronze hover:text-bronze-dark flex items-center gap-1"
          >
            <span>View All Sales</span>
            <ChevronRight size={14} />
          </button>
        }
      />
    </div>
  );
}

