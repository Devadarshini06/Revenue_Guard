import React, { useState, useEffect } from 'react';
import { Package, Award, TrendingDown, ArrowUpDown, Tag } from 'lucide-react';
import { api } from '../services/api';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function ProductInsights({ filters }) {
  const [products, setProducts] = useState([]);
  const [bestSellers, setBestSellers] = useState([]);
  const [lowPerformers, setLowPerformers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getProductPerformance(filters),
      api.getBestSellers(filters),
      api.getLowPerformers(filters)
    ])
      .then(([prodData, bestData, lowData]) => {
        if (!isMounted) return;
        setProducts(prodData || []);
        setBestSellers(bestData || []);
        setLowPerformers(lowData || []);
      })
      .catch((err) => console.error('Product insights error:', err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [filters]);

  if (loading && products.length === 0) {
    return <LoadingSpinner text="Benchmarking catalog SKU performance..." />;
  }

  const columns = [
    { key: 'rank', header: 'Rank', align: 'center', render: (v) => <span className="font-mono font-bold text-xs">#{v}</span> },
    { key: 'sku', header: 'SKU', render: (v) => <span className="font-mono text-bronze-dark font-medium">{v}</span> },
    { key: 'name', header: 'Product Name', render: (v) => <span className="font-medium text-brand-dark">{v}</span> },
    { key: 'category_name', header: 'Category' },
    { key: 'unit_price', header: 'Unit Price', align: 'right', render: (v) => `$${Number(v).toFixed(2)}` },
    { key: 'unit_cost', header: 'Unit Cost', align: 'right', render: (v) => `$${Number(v).toFixed(2)}` },
    { key: 'units_sold', header: 'Units Sold', align: 'right', render: (v) => v.toLocaleString() },
    { key: 'revenue', header: 'Net Revenue', align: 'right', render: (v) => <span className="font-semibold">${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span> },
    { key: 'profit', header: 'Profit Yield', align: 'right', render: (v) => <span className="font-medium text-emerald-700">${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span> },
    { key: 'profit_margin', header: 'Margin %', align: 'center', render: (v) => (
      <span className={`px-2 py-0.5 rounded font-mono font-bold text-xs ${
        v >= 45 ? 'bg-emerald-50 text-emerald-800' : v < 25 ? 'bg-rose-50 text-rose-800' : 'text-brand-dark'
      }`}>
        {v}%
      </span>
    )},
    { key: 'discount_rate', header: 'Discount %', align: 'center', render: (v) => <span className="font-mono text-brand-gray">{v}%</span> },
    { key: 'refund_rate', header: 'Refund %', align: 'center', render: (v) => (
      <span className={`font-mono ${v >= 5 ? 'text-rose-700 font-bold' : 'text-brand-gray'}`}>{v}%</span>
    )}
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-brand-dark">
          Product Intelligence & SKU Analytics
        </h1>
        <p className="text-xs text-brand-gray mt-0.5">
          Comprehensive SKU rankings, revenue velocity, margin contribution, and discount/refund ratios.
        </p>
      </div>

      {/* Best-Sellers vs Low-Performers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Best Sellers */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-1.5 bg-emerald-100 text-emerald-800 rounded-lg"><Award size={16} /></div>
            <div>
              <h3 className="text-sm font-semibold text-brand-dark">Top 5 Best-Selling Products</h3>
              <p className="text-[11px] text-brand-gray">Highest net revenue contributors</p>
            </div>
          </div>
          <div className="divide-y divide-border/60">
            {bestSellers.map((p, idx) => (
              <div key={p.product_id} className="py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono font-bold text-brand-gray">0{idx + 1}</span>
                  <div>
                    <div className="font-medium text-brand-dark">{p.name}</div>
                    <div className="text-[10px] text-brand-gray font-mono">{p.sku} • {p.units_sold} units</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-brand-dark">${Number(p.revenue).toLocaleString()}</div>
                  <div className="text-[10px] text-emerald-700 font-medium">{p.profit_margin}% margin</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Low Performers */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-1.5 bg-rose-100 text-rose-800 rounded-lg"><TrendingDown size={16} /></div>
            <div>
              <h3 className="text-sm font-semibold text-brand-dark">Lowest Revenue Generators</h3>
              <p className="text-[11px] text-brand-gray">Candidates for catalog optimization or repositioning</p>
            </div>
          </div>
          <div className="divide-y divide-border/60">
            {lowPerformers.map((p, idx) => (
              <div key={p.product_id} className="py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono font-bold text-brand-gray">0{idx + 1}</span>
                  <div>
                    <div className="font-medium text-brand-dark">{p.name}</div>
                    <div className="text-[10px] text-brand-gray font-mono">{p.sku} • {p.units_sold} units</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-brand-dark">${Number(p.revenue).toLocaleString()}</div>
                  <div className="text-[10px] text-brand-gray">{p.profit_margin}% margin</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Products DataTable */}
      <DataTable
        title="Full Product Performance Ledger"
        subtitle="Ranked SKU analysis with unit economics, discount usage, and return rates"
        columns={columns}
        data={products}
        pageSize={12}
      />
    </div>
  );
}

