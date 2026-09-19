import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  breadcrumbs?: { label: string; href?: string }[];
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  badge,
  actions,
  breadcrumbs,
  className = '',
}) => {
  return (
    <div className={`mb-6 pb-4 border-b border-slate-200 ${className}`}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center space-x-2 text-xs text-slate-400 mb-2">
          {breadcrumbs.map((b, i) => (
            <React.Fragment key={i}>
              {i > 0 && <span>/</span>}
              <span className={i === breadcrumbs.length - 1 ? 'font-semibold text-slate-600' : ''}>
                {b.label}
              </span>
            </React.Fragment>
          ))}
        </nav>
      )}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h1>
            {badge}
          </div>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center space-x-2 shrink-0">{actions}</div>}
      </div>
    </div>
  );
};
