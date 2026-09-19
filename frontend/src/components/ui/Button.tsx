import React from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost' | 'sage';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed select-none cursor-pointer';

  const sizeStyles = {
    sm: 'px-2.5 py-1.5 text-xs gap-1.5',
    md: 'px-3.5 py-2 text-xs font-semibold gap-2',
    lg: 'px-4 py-2.5 text-sm font-semibold gap-2.5',
  };

  const variantStyles = {
    primary: 'bg-cyan-800 hover:bg-cyan-900 text-white focus:ring-cyan-700 shadow-xs',
    secondary: 'bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 focus:ring-slate-400',
    outline: 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 focus:ring-cyan-700 shadow-xs',
    danger: 'bg-red-700 hover:bg-red-800 text-white focus:ring-red-600 shadow-xs',
    sage: 'bg-emerald-700 hover:bg-emerald-800 text-white focus:ring-emerald-600 shadow-xs',
    ghost: 'bg-transparent hover:bg-slate-100 text-slate-700 focus:ring-slate-400',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : icon}
      <span>{children}</span>
    </button>
  );
};
