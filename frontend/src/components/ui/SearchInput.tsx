import React from 'react';
import { Search, X, Filter } from 'lucide-react';

interface SearchInputProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  className?: string;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  placeholder = 'Search patients, MRN, campaigns...',
  className = '',
}) => {
  return (
    <div className={`relative flex items-center ${className}`}>
      <Search className="absolute left-3 w-4 h-4 text-slate-400 pointer-events-none" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-8 py-1.5 text-xs bg-white border border-slate-200 rounded-md focus:outline-none focus:border-cyan-700 text-slate-900 placeholder:text-slate-400"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-2.5 p-0.5 rounded-full text-slate-400 hover:text-slate-600"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};

interface FilterOption {
  label: string;
  value: string;
}

interface FilterBarProps {
  searchValue: string;
  onSearchChange: (val: string) => void;
  filterOptions?: { key: string; label: string; options: FilterOption[]; value: string; onChange: (val: string) => void }[];
  onReset?: () => void;
  className?: string;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  searchValue,
  onSearchChange,
  filterOptions = [],
  onReset,
  className = '',
}) => {
  return (
    <div className={`flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg ${className}`}>
      <div className="grow max-w-xs">
        <SearchInput value={searchValue} onChange={onSearchChange} />
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {filterOptions.map((f) => (
          <select
            key={f.key}
            value={f.value}
            onChange={(e) => f.onChange(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-md text-slate-700 focus:outline-none focus:border-cyan-700"
          >
            <option value="">{f.label}: All</option>
            {f.options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ))}
        {onReset && (
          <button
            onClick={onReset}
            className="px-2.5 py-1.5 text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1"
          >
            <Filter className="w-3 h-3" />
            Reset
          </button>
        )}
      </div>
    </div>
  );
};
