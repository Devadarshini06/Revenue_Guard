import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Database, Shield, Bell, DollarSign, CheckCircle2, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function Settings() {
  const [currency, setCurrency] = useState('USD');
  const [fiscalYearStart, setFiscalYearStart] = useState('01');
  const [marginAlertThreshold, setMarginAlertThreshold] = useState('25.0');
  const [dbStatus, setDbStatus] = useState({ status: 'Connected', latency: '1.2ms', rows: '5,200+' });
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-brand-dark">
          Platform Configuration & Parameters
        </h1>
        <p className="text-xs text-brand-gray mt-0.5">
          Manage currency display, fiscal thresholds, profit margin alert gates, and database settings.
        </p>
      </div>

      {saved && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-600" />
          <span>Platform settings updated successfully.</span>
        </div>
      )}

      {/* Database Diagnostic Status */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
        <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
          <div className="flex items-center gap-2">
            <Database size={18} className="text-bronze" />
            <h3 className="text-sm font-bold text-brand-dark">Database Connection & Diagnostic Status</h3>
          </div>
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
            Operational
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-background border border-border">
            <span className="text-brand-gray text-[10px] uppercase font-semibold">Engine / Dialect</span>
            <div className="text-brand-dark font-mono font-bold mt-1">Standalone Mock Analytics Engine</div>
          </div>
          <div className="p-3 rounded-lg bg-background border border-border">
            <span className="text-brand-gray text-[10px] uppercase font-semibold">Indexed Orders Pool</span>
            <div className="text-brand-dark font-mono font-bold mt-1">5,200 In-Memory Records</div>
          </div>
          <div className="p-3 rounded-lg bg-background border border-border">
            <span className="text-brand-gray text-[10px] uppercase font-semibold">Query Latency</span>
            <div className="text-emerald-700 font-mono font-bold mt-1">&lt; 1ms Instant Response</div>
          </div>
        </div>
      </div>

      {/* Form Settings */}
      <form onSubmit={handleSave} className="bg-card border border-border rounded-xl p-6 shadow-subtle space-y-5">
        <div>
          <h3 className="text-sm font-bold text-brand-dark mb-1">Financial Parameters</h3>
          <p className="text-xs text-brand-gray mb-4">
            Configure financial display conventions across all analytics modules.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-medium text-brand-dark mb-1">Base Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
              >
                <option value="USD">USD ($) - United States Dollar</option>
                <option value="EUR">EUR (€) - Euro</option>
                <option value="GBP">GBP (£) - British Pound</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-brand-dark mb-1">Fiscal Year Starting Month</label>
              <select
                value={fiscalYearStart}
                onChange={(e) => setFiscalYearStart(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
              >
                <option value="01">January (Calendar Year)</option>
                <option value="04">April (Q2 Start)</option>
                <option value="10">October (Federal Fiscal)</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-brand-dark mb-1">Profit Margin Alert Floor (%)</label>
              <input
                type="number"
                step="0.5"
                value={marginAlertThreshold}
                onChange={(e) => setMarginAlertThreshold(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze font-mono"
              />
              <span className="text-[10px] text-brand-gray mt-1 block">
                Products yielding below this threshold trigger an automated thin-margin alert.
              </span>
            </div>

            <div>
              <label className="block font-medium text-brand-dark mb-1">Data Model Cache Invalidation</label>
              <select className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze">
                <option>Real-Time SQL Execution (Immediate)</option>
                <option>5-Minute Aggregate Cache</option>
              </select>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-border flex justify-end">
          <button
            type="submit"
            className="px-5 py-2 bg-brand-dark text-white text-xs font-semibold rounded-lg hover:bg-black transition-colors"
          >
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
}

