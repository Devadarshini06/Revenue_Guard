import React, { useState, useEffect } from 'react';
import {
  Upload,
  FileCheck,
  AlertTriangle,
  Database,
  RefreshCw,
  Terminal,
  Play,
  CheckCircle2,
  XCircle,
  FileSpreadsheet,
  Clock,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';

const PREBUILT_SQL_QUERIES = [
  {
    name: '1. Monthly Growth (LAG Window Function)',
    query: `WITH monthly_rev AS (
    SELECT 
        substr(o.order_date, 1, 7) AS month,
        ROUND(SUM(oi.net_revenue) - COALESCE(SUM(r.refund_amount), 0), 2) AS net_revenue
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN refunds r ON oi.id = r.order_item_id
    GROUP BY substr(o.order_date, 1, 7)
)
SELECT 
    month,
    net_revenue,
    LAG(net_revenue, 1) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND(((net_revenue - LAG(net_revenue, 1) OVER (ORDER BY month)) * 100.0 / LAG(net_revenue, 1) OVER (ORDER BY month)), 2) AS growth_pct
FROM monthly_rev
ORDER BY month DESC
LIMIT 12;`
  },
  {
    name: '2. Top 10 Products by Revenue (RANK)',
    query: `SELECT 
    p.sku,
    p.name AS product_name,
    c.name AS category_name,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.net_revenue) - COALESCE(SUM(r.refund_amount), 0), 2) AS net_revenue,
    ROUND(SUM(oi.profit), 2) AS gross_profit,
    RANK() OVER (ORDER BY (SUM(oi.net_revenue) - COALESCE(SUM(r.refund_amount), 0)) DESC) AS revenue_rank
FROM products p
JOIN categories c ON p.category_id = c.id
JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN refunds r ON oi.id = r.order_item_id
GROUP BY p.id, p.sku, p.name, c.name
ORDER BY net_revenue DESC
LIMIT 10;`
  },
  {
    name: '3. Category Profit Margin Yields (CTE)',
    query: `WITH category_summary AS (
    SELECT 
        c.name AS category,
        ROUND(SUM(oi.gross_revenue), 2) AS gross_sales,
        ROUND(SUM(oi.discount_amount), 2) AS total_discounts,
        ROUND(SUM(oi.net_revenue) - COALESCE(SUM(r.refund_amount), 0), 2) AS net_revenue,
        ROUND(SUM(oi.cogs), 2) AS total_cogs
    FROM categories c
    JOIN products p ON c.id = p.category_id
    JOIN order_items oi ON p.id = oi.product_id
    LEFT JOIN refunds r ON oi.id = r.order_item_id
    GROUP BY c.id, c.name
)
SELECT 
    category,
    gross_sales,
    total_discounts,
    net_revenue,
    ROUND(net_revenue - total_cogs, 2) AS gross_profit,
    ROUND(((net_revenue - total_cogs) * 100.0 / net_revenue), 2) AS margin_percentage
FROM category_summary
ORDER BY gross_profit DESC;`
  },
  {
    name: '4. Refund Reasons & Capital Impact',
    query: `SELECT 
    r.refund_reason,
    COUNT(r.id) AS claim_count,
    ROUND(SUM(r.refund_amount), 2) AS total_refunded,
    ROUND(AVG(r.refund_amount), 2) AS avg_claim_value
FROM refunds r
GROUP BY r.refund_reason
ORDER BY total_refunded DESC;`
  }
];

export default function DataManagement() {
  const [file, setFile] = useState(null);
  const [validating, setValidating] = useState(false);
  const [validationReport, setValidationReport] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [history, setHistory] = useState([]);
  const [reseeding, setReseeding] = useState(false);
  const [reseedSuccess, setReseedSuccess] = useState(false);

  // SQL Query Runner state
  const [sqlQuery, setSqlQuery] = useState(PREBUILT_SQL_QUERIES[0].query);
  const [sqlResult, setSqlResult] = useState(null);
  const [sqlError, setSqlError] = useState(null);
  const [sqlRunning, setSqlRunning] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = () => {
    api.getUploadHistory()
      .then(data => setHistory(data || []))
      .catch(err => console.error('Upload history error:', err));
  };

  const handleFileChange = async (e) => {
    const selected = e.target.files[0];
    if (!selected) return;

    if (selected.size > 10 * 1024 * 1024) {
      alert('File size exceeds the maximum allowed limit of 10MB.');
      e.target.value = '';
      return;
    }

    setFile(selected);
    setValidating(true);
    setValidationReport(null);

    try {
      const report = await api.validateDataset(selected);
      setValidationReport(report);
    } catch (err) {
      alert(`Validation error: ${err.message}`);
    } finally {
      setValidating(false);
    }
  };

  const handleImport = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await api.uploadDataset(file);
      alert('Dataset validated and imported successfully!');
      setFile(null);
      setValidationReport(null);
      loadHistory();
    } catch (err) {
      alert(`Import error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleReseed = async () => {
    if (!window.confirm('This will refresh the database with 5,200 fresh synthetic enterprise orders. Proceed?')) return;
    setReseeding(true);
    setReseedSuccess(false);
    try {
      await api.reseedData();
      setReseedSuccess(true);
      loadHistory();
      setTimeout(() => setReseedSuccess(false), 4000);
    } catch (err) {
      alert(`Reseed failed: ${err.message}`);
    } finally {
      setReseeding(false);
    }
  };

  const handleRunSQL = async () => {
    setSqlRunning(true);
    setSqlError(null);
    setSqlResult(null);
    try {
      const res = await api.executeSQL(sqlQuery);
      setSqlResult(res);
    } catch (err) {
      setSqlError(err.message);
    } finally {
      setSqlRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-brand-dark">
            Data Management, Ingestion & SQL Query Engine
          </h1>
          <p className="text-xs text-brand-gray mt-0.5">
            Validate dataset schemas, detect duplicates and anomalies, inspect upload logs, and run analytical SQL CTEs.
          </p>
        </div>

        {/* Reseed 1-click synthetic dataset */}
        <button
          onClick={handleReseed}
          disabled={reseeding}
          className="flex items-center gap-2 px-3.5 py-2 bg-background border border-border rounded-lg text-xs font-semibold text-brand-dark hover:bg-card hover:border-bronze transition-colors shadow-2xs shrink-0"
        >
          <RefreshCw size={14} className={reseeding ? 'animate-spin text-bronze' : ''} />
          <span>{reseeding ? 'Generating 5,200 Orders...' : 'Regenerate 5,200 Sample Orders'}</span>
        </button>
      </div>

      {reseedSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-600" />
          <span>Sample dataset successfully re-seeded with 5,200 enterprise transactions and relational models!</span>
        </div>
      )}

      {/* Upload and Validation Card */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-subtle">
        <div className="flex items-center gap-2 mb-2">
          <Upload size={18} className="text-bronze" />
          <h2 className="text-sm font-bold text-brand-dark">Dataset Upload & Pre-Flight Validation</h2>
        </div>
        <p className="text-xs text-brand-gray mb-4">
          Upload CSV or Excel spreadsheets. Our pipeline automatically inspects missing columns, data types, duplicate primary keys, and assigns a Data Quality Score.
        </p>

        {/* Dropzone */}
        <label className="border-2 border-dashed border-border hover:border-bronze rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors bg-background/50">
          <FileSpreadsheet size={32} className="text-brand-gray mb-2" />
          <span className="text-xs font-medium text-brand-dark">
            {file ? file.name : 'Click to select CSV or Excel (.xlsx) file to validate'}
          </span>
          <span className="text-[11px] text-brand-gray mt-1">
            Accepts UTF-8 CSV, XLS, XLSX formats up to 10MB
          </span>
          <input
            type="file"
            accept=".csv, .xlsx, .xls"
            onChange={handleFileChange}
            className="hidden"
          />
        </label>

        {validating && (
          <div className="mt-4"><LoadingSpinner text="Running automated schema validation..." size={20} /></div>
        )}

        {/* Validation Report */}
        {validationReport && (
          <div className="mt-6 border-t border-border pt-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileCheck size={18} className="text-emerald-600" />
                <span className="text-xs font-bold text-brand-dark">Validation Complete: {validationReport.filename}</span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full font-mono text-xs font-bold">
                Quality Score: {validationReport.quality_score}%
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-background border border-border rounded-lg text-xs">
                <div className="text-brand-gray text-[10px] uppercase font-semibold">Total Rows</div>
                <div className="text-base font-bold text-brand-dark mt-0.5">{validationReport.total_rows.toLocaleString()}</div>
              </div>
              <div className="p-3 bg-background border border-border rounded-lg text-xs">
                <div className="text-brand-gray text-[10px] uppercase font-semibold">Valid Clean Rows</div>
                <div className="text-base font-bold text-emerald-700 mt-0.5">{validationReport.valid_rows.toLocaleString()}</div>
              </div>
              <div className="p-3 bg-background border border-border rounded-lg text-xs">
                <div className="text-brand-gray text-[10px] uppercase font-semibold">Duplicate Records</div>
                <div className="text-base font-bold text-amber-700 mt-0.5">{validationReport.duplicate_rows}</div>
              </div>
              <div className="p-3 bg-background border border-border rounded-lg text-xs">
                <div className="text-brand-gray text-[10px] uppercase font-semibold">Invalid / Negative Rows</div>
                <div className="text-base font-bold text-rose-700 mt-0.5">{validationReport.invalid_rows}</div>
              </div>
            </div>

            {/* Preview table */}
            {validationReport.preview && validationReport.preview.length > 0 && (
              <div className="mt-4">
                <div className="text-xs font-semibold text-brand-dark mb-2">Dataset Preview (Top Rows):</div>
                <div className="overflow-x-auto border border-border rounded-lg">
                  <table className="w-full text-[11px] text-left text-brand-dark">
                    <thead className="bg-background text-brand-gray uppercase font-mono font-medium">
                      <tr>
                        {Object.keys(validationReport.preview[0]).map(k => (
                          <th key={k} className="px-3 py-2 border-b border-border">{k}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {validationReport.preview.map((row, idx) => (
                        <tr key={idx} className="hover:bg-background/50">
                          {Object.values(row).map((val, cIdx) => (
                            <td key={cIdx} className="px-3 py-1.5 font-mono">{val !== null ? String(val) : '—'}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={handleImport}
                disabled={uploading}
                className="px-4 py-2 bg-brand-dark text-white rounded-lg text-xs font-semibold hover:bg-black transition-colors"
              >
                {uploading ? 'Ingesting into Database...' : 'Commit & Import Validated Data'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Upload History Table */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
        <div className="flex items-center gap-2 mb-3">
          <Clock size={16} className="text-bronze" />
          <h3 className="text-sm font-bold text-brand-dark">Data Ingestion Audit History</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-brand-dark">
            <thead className="bg-background border-b border-border text-[11px] uppercase tracking-wider text-brand-gray font-semibold">
              <tr>
                <th className="px-4 py-3">Filename</th>
                <th className="px-4 py-3">Uploaded At</th>
                <th className="px-4 py-3 text-right">Total Rows</th>
                <th className="px-4 py-3 text-right">Valid Rows</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {history.map((h) => (
                <tr key={h.id} className="hover:bg-background/50">
                  <td className="px-4 py-3 font-mono font-medium">{h.filename}</td>
                  <td className="px-4 py-3 text-brand-gray">{h.upload_date}</td>
                  <td className="px-4 py-3 text-right font-mono">{h.rows_count.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right font-mono text-emerald-700">{h.valid_rows.toLocaleString()}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {h.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-brand-gray text-[11px]">{h.summary_notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* SQL Analytics Query Explorer & Runner */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-subtle">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Terminal size={18} className="text-bronze" />
              <h2 className="text-sm font-bold text-brand-dark">Interactive SQL Analytics Runner</h2>
            </div>
            <p className="text-xs text-brand-gray mt-0.5">
              Execute parameterized SQL CTEs, window functions (LAG, RANK), and multi-table joins against PostgreSQL / SQLite.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <select
              onChange={(e) => {
                const selected = PREBUILT_SQL_QUERIES.find(q => q.name === e.target.value);
                if (selected) setSqlQuery(selected.query);
              }}
              className="px-2.5 py-1.5 text-xs bg-background border border-border rounded-lg text-brand-dark focus:outline-none"
            >
              {PREBUILT_SQL_QUERIES.map(q => (
                <option key={q.name} value={q.name}>{q.name}</option>
              ))}
            </select>

            <button
              onClick={handleRunSQL}
              disabled={sqlRunning}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-dark text-white rounded-lg text-xs font-semibold hover:bg-black transition-colors"
            >
              <Play size={13} fill="currentColor" />
              <span>{sqlRunning ? 'Executing...' : 'Run Query'}</span>
            </button>
          </div>
        </div>

        {/* Code editor area */}
        <textarea
          value={sqlQuery}
          onChange={(e) => setSqlQuery(e.target.value)}
          rows={8}
          className="w-full p-3 font-mono text-xs bg-[#231F1D] text-[#E5E1DD] rounded-xl border border-border focus:outline-none focus:border-bronze leading-relaxed select-text"
          placeholder="SELECT ... FROM ...;"
        />

        {sqlError && (
          <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 font-mono">
            {sqlError}
          </div>
        )}

        {/* Results */}
        {sqlResult && (
          <div className="mt-4 border-t border-border pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-brand-dark">Query Results ({sqlResult.row_count} rows returned):</span>
              <span className="text-[10px] font-mono text-brand-gray">Executed in read-only transaction</span>
            </div>

            <div className="overflow-x-auto border border-border rounded-lg max-h-80">
              <table className="w-full text-left text-xs text-brand-dark">
                <thead className="bg-[#FAF9F6] border-b border-border text-[11px] uppercase tracking-wider text-brand-gray font-semibold font-mono sticky top-0">
                  <tr>
                    {sqlResult.columns.map(c => (
                      <th key={c} className="px-3 py-2">{c}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {sqlResult.rows.map((r, rIdx) => (
                    <tr key={rIdx} className="hover:bg-background/60">
                      {sqlResult.columns.map(c => (
                        <td key={c} className="px-3 py-1.5 font-mono text-[11px]">
                          {r[c] !== null ? String(r[c]) : 'NULL'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

