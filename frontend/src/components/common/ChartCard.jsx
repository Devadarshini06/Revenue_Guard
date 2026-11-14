import React from 'react';

export default function ChartCard({
  title,
  subtitle,
  action,
  children,
  className = "",
  height = "h-72"
}) {
  return (
    <div className={`bg-card border border-border rounded-xl p-5 shadow-subtle ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-sm font-semibold text-brand-dark tracking-tight">
            {title}
          </h3>
          {subtitle && (
            <p className="text-xs text-brand-gray mt-0.5">
              {subtitle}
            </p>
          )}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>

      <div className={`w-full ${height}`}>
        {children}
      </div>
    </div>
  );
}

