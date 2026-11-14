import React from 'react';
import { Sparkles, AlertTriangle, CheckCircle2, Info, ArrowUpRight } from 'lucide-react';

export default function InsightBanner({ insights = [], loading = false }) {
  if (loading) {
    return (
      <div className="bg-card border border-border rounded-xl p-5 shadow-subtle animate-pulse mb-6">
        <div className="h-5 bg-gray-200 rounded w-48 mb-3"></div>
        <div className="h-16 bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  if (!insights || insights.length === 0) return null;

  const typeConfig = {
    success: {
      border: 'border-emerald-200',
      bg: 'bg-emerald-50/60',
      iconColor: 'text-emerald-700',
      badgeBg: 'bg-emerald-100/80 text-emerald-800',
      icon: CheckCircle2,
    },
    warning: {
      border: 'border-amber-200',
      bg: 'bg-amber-50/60',
      iconColor: 'text-amber-700',
      badgeBg: 'bg-amber-100/80 text-amber-800',
      icon: AlertTriangle,
    },
    danger: {
      border: 'border-rose-200',
      bg: 'bg-rose-50/60',
      iconColor: 'text-rose-700',
      badgeBg: 'bg-rose-100/80 text-rose-800',
      icon: AlertTriangle,
    },
    info: {
      border: 'border-blue-200',
      bg: 'bg-blue-50/60',
      iconColor: 'text-blue-700',
      badgeBg: 'bg-blue-100/80 text-blue-800',
      icon: Info,
    },
  };

  return (
    <div className="bg-card border border-border rounded-xl p-5 shadow-subtle mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-bronze/15 text-bronze-dark rounded-md">
            <Sparkles size={16} />
          </div>
          <h3 className="text-sm font-semibold text-brand-dark tracking-tight">
            Intelligent Business Insights
          </h3>
          <span className="text-xs bg-background border border-border px-2 py-0.5 rounded-full text-brand-gray font-mono">
            {insights.length} active detections
          </span>
        </div>
        <span className="text-[11px] text-brand-gray">
          Generated in real-time from analytical models
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {insights.map((ins) => {
          const cfg = typeConfig[ins.type] || typeConfig.info;
          const IconComp = cfg.icon;

          return (
            <div
              key={ins.id}
              className={`border ${cfg.border} ${cfg.bg} rounded-lg p-3.5 flex flex-col justify-between transition-all hover:shadow-sm`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded ${cfg.badgeBg}`}>
                    {ins.category}
                  </span>
                  {ins.metric_value && (
                    <span className="text-xs font-mono font-bold text-brand-dark">
                      {ins.metric_value}
                    </span>
                  )}
                </div>

                <div className="flex items-start gap-2 mb-1">
                  <IconComp size={15} className={`${cfg.iconColor} shrink-0 mt-0.5`} />
                  <h4 className="text-xs font-semibold text-brand-dark leading-snug">
                    {ins.title}
                  </h4>
                </div>

                <p className="text-xs text-brand-gray leading-relaxed pl-5 mb-2">
                  {ins.description}
                </p>
              </div>

              {ins.recommendation && (
                <div className="mt-2 pt-2 border-t border-black/5 text-[11px] text-brand-dark flex items-start gap-1">
                  <span className="font-semibold text-bronze-dark shrink-0">Action:</span>
                  <span className="text-brand-gray italic">{ins.recommendation}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

