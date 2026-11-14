import React, { useState } from 'react';
import {
  FileSpreadsheet,
  Download,
  FileText,
  Database,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowRight,
  Sparkles,
  Eye,
  X
} from 'lucide-react';
import { api } from '../services/api';

export default function ReportsExports({ filters }) {
  const [downloading, setDownloading] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [generatingSummary, setGeneratingSummary] = useState(false);
  const [showPowerBIModal, setShowPowerBIModal] = useState(false);
  const [powerBIData, setPowerBIData] = useState(null);

  const handleDownloadCsv = () => {
    setDownloading('csv');
    try {
      api.exportTransactionsCSV();
    } finally {
      setTimeout(() => setDownloading(null), 800);
    }
  };

  const handleDownloadExcel = () => {
    setDownloading('excel');
    try {
      api.exportTransactionsExcel();
    } finally {
      setTimeout(() => setDownloading(null), 800);
    }
  };

  const handleGenerateSummary = async () => {
    setGeneratingSummary(true);
    try {
      const data = await api.getExecutiveReport(filters);
      setSummaryData(data);
    } catch (err) {
      console.error('Failed to generate summary:', err);
    } finally {
      setGeneratingSummary(false);
    }
  };

  const handleOpenPowerBI = async () => {
    const data = await api.getPowerBIDataset();
    setPowerBIData(data);
    setShowPowerBIModal(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-brand-dark">
          Reports, Business Intelligence & Data Exports
        </h1>
        <p className="text-xs text-brand-gray mt-0.5">
          Generate board-ready performance summaries and export Power BI-compliant relational datasets (Offline Mock Engine).
        </p>
      </div>

      {/* Export Options Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* CSV Export Card */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center mb-4">
              <FileSpreadsheet size={20} />
            </div>
            <h3 className="text-sm font-bold text-brand-dark mb-1">
              CSV Transaction Export
            </h3>
            <p className="text-xs text-brand-gray leading-relaxed mb-4">
              Download complete raw ledger rows with customer references, product line items, discounts, and settlements.
            </p>
          </div>

          <button
            onClick={handleDownloadCsv}
            disabled={downloading === 'csv'}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-background border border-border rounded-lg text-xs font-semibold text-brand-dark hover:bg-card hover:border-bronze transition-colors shadow-2xs"
          >
            <Download size={14} className={downloading === 'csv' ? 'animate-bounce' : ''} />
            <span>{downloading === 'csv' ? 'Exporting...' : 'Download CSV (.csv)'}</span>
          </button>
        </div>

        {/* Excel BI Workbook Export Card */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center mb-4">
              <Layers size={20} />
            </div>
            <h3 className="text-sm font-bold text-brand-dark mb-1">
              Multi-Sheet Excel BI Workbook
            </h3>
            <p className="text-xs text-brand-gray leading-relaxed mb-4">
              Structured spreadsheet formatted with dedicated sheets for Transactions, Monthly Trends, and Category Yields.
            </p>
          </div>

          <button
            onClick={handleDownloadExcel}
            disabled={downloading === 'excel'}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-brand-dark text-white rounded-lg text-xs font-semibold hover:bg-black transition-colors shadow-2xs"
          >
            <Download size={14} className={downloading === 'excel' ? 'animate-bounce' : ''} />
            <span>{downloading === 'excel' ? 'Exporting...' : 'Download Excel (.xlsx)'}</span>
          </button>
        </div>

        {/* Power BI Ready Dataset Card */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-subtle flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center mb-4">
              <Database size={20} />
            </div>
            <h3 className="text-sm font-bold text-brand-dark mb-1">
              Power BI Ready Dataset
            </h3>
            <p className="text-xs text-brand-gray leading-relaxed mb-4">
              Direct dimensional Star-Schema data model formatted with keys for instant import into Microsoft Power BI Desktop.
            </p>
          </div>

          <button
            onClick={handleOpenPowerBI}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-background border border-border rounded-lg text-xs font-semibold text-brand-dark hover:bg-card hover:border-bronze transition-colors shadow-2xs"
          >
            <Eye size={14} />
            <span>Inspect Power BI Dataset</span>
          </button>
        </div>
      </div>

      {/* Monthly Summary Generator Section */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-subtle">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
          <div>
            <div className="flex items-center gap-2">
              <FileText size={18} className="text-bronze" />
              <h2 className="text-sm font-bold text-brand-dark">Executive Financial Brief Generator</h2>
            </div>
            <p className="text-xs text-brand-gray mt-0.5">
              Instantly compile executive KPI metrics and category performance into a structured snapshot.
            </p>
          </div>

          <button
            onClick={handleGenerateSummary}
            disabled={generatingSummary}
            className="flex items-center gap-2 px-4 py-2 bg-bronze text-white text-xs font-semibold rounded-lg hover:bg-bronze-hover transition-colors shrink-0"
          >
            <Sparkles size={14} />
            <span>{generatingSummary ? 'Compiling Brief...' : 'Generate Performance Brief'}</span>
          </button>
        </div>

        {summaryData ? (
          <div className="mt-5 space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-background border border-border">
              <div className="flex items-center gap-2 text-xs text-brand-dark">
                <CheckCircle2 size={16} className="text-emerald-600" />
                <span className="font-semibold">Executive Performance Brief compiled successfully</span>
              </div>
              <span className="text-[11px] font-mono text-brand-gray">
                Generated at: {new Date(summaryData.generated_at).toLocaleString()}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-lg border border-border bg-card">
                <div className="text-brand-gray text-[11px]">Net Revenue</div>
                <div className="text-base font-bold text-brand-dark mt-1">
                  {summaryData.kpis?.net_revenue?.formatted_value}
                </div>
              </div>
              <div className="p-3 rounded-lg border border-border bg-card">
                <div className="text-brand-gray text-[11px]">Gross Margin</div>
                <div className="text-base font-bold text-brand-dark mt-1">
                  {summaryData.kpis?.profit_margin?.formatted_value}
                </div>
              </div>
              <div className="p-3 rounded-lg border border-border bg-card">
                <div className="text-brand-gray text-[11px]">Total Transactions</div>
                <div className="text-base font-bold text-brand-dark mt-1">
                  {summaryData.kpis?.total_orders?.formatted_value}
                </div>
              </div>
              <div className="p-3 rounded-lg border border-border bg-card">
                <div className="text-brand-gray text-[11px]">Average Order Value</div>
                <div className="text-base font-bold text-brand-dark mt-1">
                  {summaryData.kpis?.average_order_value?.formatted_value}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-brand-gray italic">
            Click 'Generate Performance Brief' to evaluate all filtered records and compile the summary.
          </div>
        )}
      </div>

      {/* Power BI Dataset Inspector Modal */}
      {showPowerBIModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-card border border-border rounded-xl shadow-elevated w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database size={16} className="text-amber-600" />
                <h3 className="text-sm font-bold text-brand-dark">Power BI Star-Schema Dimensional Dataset</h3>
              </div>
              <button
                onClick={() => setShowPowerBIModal(false)}
                className="p-1 text-brand-gray hover:text-brand-dark rounded"
              >
                <X size={16} />
              </button>
            </div>

            <div className="p-4 overflow-y-auto flex-1 font-mono text-xs">
              <div className="mb-2 text-[11px] text-brand-gray font-sans">
                Sample preview of transactional dimensional attributes ready for Power BI OData or JSON ingestion:
              </div>
              <pre className="p-3 bg-[#231F1D] text-[#E5E1DD] rounded-lg overflow-x-auto text-[11px] leading-relaxed">
                {JSON.stringify(powerBIData?.slice(0, 3), null, 2)}
              </pre>
            </div>

            <div className="p-3 border-t border-border bg-background flex justify-end">
              <button
                onClick={() => setShowPowerBIModal(false)}
                className="px-4 py-1.5 bg-brand-dark text-white rounded-lg text-xs font-semibold"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
