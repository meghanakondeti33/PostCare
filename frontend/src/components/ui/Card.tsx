import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({ children, className = '', onClick }) => (
  <div
    onClick={onClick}
    className={`bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden ${
      onClick ? 'cursor-pointer hover:border-slate-300 hover:shadow-sm transition-all' : ''
    } ${className}`}
  >
    {children}
  </div>
);

export const CardHeader: React.FC<{ children: React.ReactNode; className?: string; action?: React.ReactNode }> = ({
  children,
  className = '',
  action,
}) => (
  <div className={`px-5 py-4 border-b border-slate-100 flex items-center justify-between ${className}`}>
    <div>{children}</div>
    {action && <div>{action}</div>}
  </div>
);

export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <h3 className={`text-sm font-bold text-slate-900 tracking-tight ${className}`}>{children}</h3>
);

export const CardDescription: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <p className={`text-xs text-slate-500 mt-0.5 ${className}`}>{children}</p>
);

export const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`p-5 ${className}`}>{children}</div>
);

export const CardFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`px-5 py-3 bg-slate-50 border-t border-slate-100 text-xs text-slate-600 flex items-center justify-between ${className}`}>
    {children}
  </div>
);
