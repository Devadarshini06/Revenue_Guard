/**
 * Client-side file export utilities (CSV / Excel format)
 */

export function downloadCSV(filename, data) {
  if (!data || !data.length) {
    alert('No records available to export.');
    return;
  }

  const headers = Object.keys(data[0]);
  const csvRows = [];
  csvRows.push(headers.join(','));

  for (const row of data) {
    const values = headers.map(header => {
      const escaped = ('' + (row[header] ?? '')).replace(/"/g, '""');
      return `"${escaped}"`;
    });
    csvRows.push(values.join(','));
  }

  const csvString = csvRows.join('\n');
  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename.endsWith('.csv') ? filename : `${filename}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export function downloadMockExcel(filename, sheetName, data) {
  // Generates clean CSV formatted with Excel mime-type for native spreadsheet opening
  if (!data || !data.length) {
    alert('No data available to export.');
    return;
  }
  downloadCSV(filename.endsWith('.csv') ? filename : `${filename}.csv`, data);
}

