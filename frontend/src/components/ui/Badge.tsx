import React from 'react';

export type BadgeVariant = 'sage' | 'amber' | 'coral' | 'lavender' | 'eucalyptus' | 'slate' | 'info' | 'purple';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'slate',
  size = 'md',
  icon,
  className = '',
}) => {
  const variantStyles: Record<BadgeVariant, string> = {
    sage: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    amber: 'bg-amber-50 text-amber-800 border-amber-200',
    coral: 'bg-red-50 text-red-800 border-red-200',
    lavender: 'bg-purple-50 text-purple-800 border-purple-200',
    purple: 'bg-purple-100 text-purple-900 border-purple-300',
    eucalyptus: 'bg-cyan-50 text-cyan-800 border-cyan-200',
    slate: 'bg-slate-100 text-slate-700 border-slate-200',
    info: 'bg-sky-50 text-sky-800 border-sky-200',
  };

  const sizeStyles = {
    sm: 'px-1.5 py-0.5 text-[10px] font-semibold gap-1',
    md: 'px-2.5 py-1 text-xs font-semibold gap-1.5',
  };

  return (
    <span
      className={`inline-flex items-center rounded-md border tracking-wide uppercase ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {icon}
      <span>{children}</span>
    </span>
  );
};

export const StatusBadge: React.FC<{ status: string; className?: string }> = ({ status, className = '' }) => {
  const norm = status?.toUpperCase() || '';
  
  if (norm.includes('HIGH') || norm.includes('URGENT') || norm.includes('ESCALATED') || norm.includes('FAIL') || norm.includes('RISK')) {
    return <Badge variant="coral" className={className}>{status}</Badge>;
  }
  if (norm.includes('MEDIUM') || norm.includes('MODERATE') || norm.includes('RETRY') || norm.includes('WAITING') || norm.includes('ATTENTION') || norm.includes('QUEUED')) {
    return <Badge variant="amber" className={className}>{status}</Badge>;
  }
  if (norm.includes('LOW') || norm.includes('RESOLVED') || norm.includes('COMPLETED') || norm.includes('SUCCESS') || norm.includes('SAFE') || norm.includes('ACTIVE')) {
    return <Badge variant="sage" className={className}>{status}</Badge>;
  }
  if (norm.includes('AI') || norm.includes('ASSESSMENT') || norm.includes('ANALYSIS')) {
    return <Badge variant="lavender" className={className}>{status}</Badge>;
  }
  if (norm.includes('IN_PROGRESS') || norm.includes('CALLING') || norm.includes('PROCESSING')) {
    return <Badge variant="eucalyptus" className={className}>{status}</Badge>;
  }
  
  return <Badge variant="slate" className={className}>{status}</Badge>;
};
