import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, ArrowUpDown, Search } from 'lucide-react';

export default function DataTable({
  columns,
  data = [],
  searchable = true,
  searchPlaceholder = "Search records...",
  pageSize = 10,
  title,
  subtitle,
  actions
}) {
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortKey, setSortKey] = useState(null);
  const [sortOrder, setSortOrder] = useState('asc'); // 'asc' or 'desc'

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  const filteredData = useMemo(() => {
    if (!search) return data;
    const lower = search.toLowerCase();
    return data.filter((row) =>
      Object.values(row).some(
        (val) => val !== null && val !== undefined && String(val).toLowerCase().includes(lower)
      )
    );
  }, [data, search]);

  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;
    return [...filteredData].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;
      
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
      }
      return sortOrder === 'asc'
        ? String(aVal).localeCompare(String(bVal))
        : String(bVal).localeCompare(String(aVal));
    });
  }, [filteredData, sortKey, sortOrder]);

  const totalPages = Math.max(1, Math.ceil(sortedData.length / pageSize));
  const paginatedData = sortedData.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="bg-card border border-border rounded-xl shadow-subtle overflow-hidden">
      {(title || searchable || actions) && (
        <div className="p-4 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            {title && (
              <h3 className="text-sm font-semibold text-brand-dark tracking-tight">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-brand-gray mt-0.5">{subtitle}</p>
            )}
          </div>

          <div className="flex items-center gap-2">
            {searchable && (
              <div className="relative">
                <Search size={14} className="absolute left-2.5 top-2.5 text-brand-gray" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setCurrentPage(1);
                  }}
                  placeholder={searchPlaceholder}
                  className="pl-8 pr-3 py-1.5 text-xs bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze w-52 sm:w-64"
                />
              </div>
            )}
            {actions}
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-brand-dark">
          <thead className="bg-[#FAF9F6] border-b border-border text-[11px] uppercase tracking-wider text-brand-gray font-semibold select-none">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => col.sortable !== false && handleSort(col.key)}
                  className={`px-4 py-3 ${
                    col.sortable !== false ? 'cursor-pointer hover:text-brand-dark' : ''
                  } ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : ''}`}
                >
                  <div className={`inline-flex items-center gap-1 ${col.align === 'right' ? 'justify-end' : ''}`}>
                    <span>{col.header}</span>
                    {col.sortable !== false && (
                      <ArrowUpDown size={11} className="opacity-50 hover:opacity-100" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-brand-gray italic">
                  No records match your criteria.
                </td>
              </tr>
            ) : (
              paginatedData.map((row, idx) => (
                <tr key={idx} className="hover:bg-background/80 transition-colors">
                  {columns.map((col) => {
                    const val = row[col.key];
                    return (
                      <td
                        key={col.key}
                        className={`px-4 py-3 ${
                          col.align === 'right'
                            ? 'text-right font-mono'
                            : col.align === 'center'
                            ? 'text-center'
                            : ''
                        }`}
                      >
                        {col.render ? col.render(val, row) : val !== null && val !== undefined ? String(val) : '—'}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="p-3 border-t border-border bg-[#FAF9F6]/50 flex items-center justify-between text-xs text-brand-gray">
        <span>
          Showing <span className="font-medium text-brand-dark">{Math.min(sortedData.length, (currentPage - 1) * pageSize + 1)}</span> to{' '}
          <span className="font-medium text-brand-dark">{Math.min(sortedData.length, currentPage * pageSize)}</span> of{' '}
          <span className="font-medium text-brand-dark">{sortedData.length}</span> records
        </span>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-1 rounded border border-border bg-card text-brand-dark disabled:opacity-40 disabled:cursor-not-allowed hover:bg-background"
          >
            <ChevronLeft size={14} />
          </button>
          <span className="px-2 font-mono text-[11px]">
            {currentPage} / {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="p-1 rounded border border-border bg-card text-brand-dark disabled:opacity-40 disabled:cursor-not-allowed hover:bg-background"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

