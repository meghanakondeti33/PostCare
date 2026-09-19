import React from 'react';

export interface Column<T> {
  header: string;
  accessor?: keyof T;
  cell?: (row: T, index: number) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string | number;
  emptyText?: string;
  onRowClick?: (item: T) => void;
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  emptyText = 'No data available',
  onRowClick,
  className = '',
}: DataTableProps<T>) {
  return (
    <div className={`overflow-x-auto rounded-lg border border-slate-200 bg-white ${className}`}>
      <table className="w-full text-left text-xs text-slate-700">
        <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} className={`px-4 py-3 ${col.className || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-slate-400">
                {emptyText}
              </td>
            </tr>
          ) : (
            data.map((row, rowIdx) => (
              <tr
                key={keyExtractor(row)}
                onClick={() => onRowClick && onRowClick(row)}
                className={`hover:bg-slate-50/80 transition-colors ${
                  onRowClick ? 'cursor-pointer' : ''
                }`}
              >
                {columns.map((col, colIdx) => (
                  <td key={colIdx} className={`px-4 py-3 align-middle ${col.className || ''}`}>
                    {col.cell ? col.cell(row, rowIdx) : col.accessor ? String(row[col.accessor] ?? '') : null}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
