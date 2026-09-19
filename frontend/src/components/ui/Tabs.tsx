import React from 'react';

export interface TabItem {
  id: string;
  label: string;
  count?: number;
  badge?: React.ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onChange, className = '' }) => {
  return (
    <div className={`border-b border-slate-200 ${className}`}>
      <nav className="-mb-px flex space-x-6 overflow-x-auto">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors flex items-center space-x-2 cursor-pointer ${
                isActive
                  ? 'border-cyan-800 text-cyan-900'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                    isActive ? 'bg-cyan-100 text-cyan-900' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {tab.count}
                </span>
              )}
              {tab.badge}
            </button>
          );
        })}
      </nav>
    </div>
  );
};
