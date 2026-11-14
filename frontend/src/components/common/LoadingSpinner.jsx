import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ text = "Loading data models...", size = 24 }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <Loader2 size={size} className="animate-spin text-bronze mb-3" />
      <span className="text-xs font-medium text-brand-gray tracking-wide">
        {text}
      </span>
    </div>
  );
}

