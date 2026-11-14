import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function KPICard({
  title,
  kpi,
  icon: Icon,
  subtitle = "vs previous period",
  loading = false
}) {
  if (loading || !kpi) {
    return (
      <div className="bg-card border border-border rounded-xl p-5 shadow-subtle animate-pulse">
        <div className="flex justify-between items-start mb-3">
          <div className="h-4 bg-gray-200 rounded w-24"></div>
          <div className="h-8 w-8 bg-gray-100 rounded-lg"></div>
        </div>
        <div className="h-8 bg-gray-200 rounded w-32 mb-2"></div>
        <div className="h-4 bg-gray-100 rounded w-28"></div>
      </div>
    );
  }

  const { formatted_value, formatted_change, is_positive, change_percentage } = kpi;
  const isZero = change_percentage === 0;

  return (
    <div className="bg-card border border-border rounded-xl p-5 shadow-subtle hover:shadow-card transition-shadow duration-200 group relative">
      <div className="flex justify-between items-start mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-brand-gray">
          {title}
        </span>
        {Icon && (
          <div className="p-2 bg-background border border-border/60 rounded-lg text-bronze group-hover:bg-bronze/10 transition-colors">
            <Icon size={16} />
          </div>
        )}
      </div>

      <div className="text-2xl font-bold tracking-tight text-brand-dark mb-2">
        {formatted_value}
      </div>

      <div className="flex items-center gap-2 text-xs">
        <span
          className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full font-medium ${
            isZero
              ? 'bg-gray-100 text-gray-600'
              : is_positive
              ? 'bg-emerald-50 text-emerald-700'
              : 'bg-rose-50 text-rose-700'
          }`}
        >
          {isZero ? (
            <Minus size={12} />
          ) : is_positive ? (
            <TrendingUp size={12} />
          ) : (
            <TrendingDown size={12} />
          )}
          {formatted_change}
        </span>
        <span className="text-brand-gray/80 text-[11px] truncate">
          {subtitle}
        </span>
      </div>
    </div>
  );
}

