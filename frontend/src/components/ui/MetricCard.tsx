import React from 'react';
import { Card } from './Card';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
    isNegative?: boolean;
  };
  variant?: 'default' | 'sage' | 'amber' | 'coral' | 'eucalyptus' | 'lavender';
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtext,
  icon,
  trend,
  variant = 'default',
  className = '',
}) => {
  const borderVariants = {
    default: 'border-slate-200',
    sage: 'border-emerald-300 bg-emerald-50/20',
    amber: 'border-amber-300 bg-amber-50/20',
    coral: 'border-red-300 bg-red-50/20',
    eucalyptus: 'border-cyan-300 bg-cyan-50/20',
    lavender: 'border-purple-300 bg-purple-50/20',
  };

  const iconBgVariants = {
    default: 'bg-slate-100 text-slate-600',
    sage: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700',
    coral: 'bg-red-100 text-red-700',
    eucalyptus: 'bg-cyan-100 text-cyan-700',
    lavender: 'bg-purple-100 text-purple-700',
  };

  return (
    <Card className={`${borderVariants[variant]} ${className}`}>
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</span>
          {icon && <div className={`p-2 rounded-md ${iconBgVariants[variant]}`}>{icon}</div>}
        </div>
        <div className="flex items-baseline justify-between">
          <div className="text-2xl font-bold text-slate-900 tracking-tight">{value}</div>
          {trend && (
            <span
              className={`text-xs font-semibold px-1.5 py-0.5 rounded ${
                trend.isNegative
                  ? 'bg-red-50 text-red-700'
                  : trend.isPositive
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              {trend.value}
            </span>
          )}
        </div>
        {subtext && <p className="text-xs text-slate-500 mt-1 font-normal">{subtext}</p>}
      </div>
    </Card>
  );
};
