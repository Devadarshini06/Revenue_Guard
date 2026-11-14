import React from 'react';
import { Inbox } from 'lucide-react';

export default function EmptyState({
  title = "No Data Found",
  description = "No records match the current filter or criteria.",
  action
}) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-card border border-border rounded-xl shadow-subtle">
      <div className="w-12 h-12 rounded-xl bg-background border border-border flex items-center justify-center text-brand-gray mb-3">
        <Inbox size={22} className="text-bronze" />
      </div>
      <h3 className="text-sm font-semibold text-brand-dark mb-1">{title}</h3>
      <p className="text-xs text-brand-gray max-w-sm mb-4 leading-relaxed">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
}

