import React from 'react';
import { Inbox, Loader2, AlertCircle } from 'lucide-react';

export const EmptyState: React.FC<{
  title?: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}> = ({
  title = 'No items found',
  description = 'There are no records matching your request or filter criteria.',
  action,
  icon = <Inbox className="w-10 h-10 text-slate-300" />,
}) => (
  <div className="flex flex-col items-center justify-center py-12 px-4 text-center border border-dashed border-slate-200 rounded-lg bg-slate-50/50">
    <div className="mb-3 p-3 bg-white rounded-full shadow-xs border border-slate-100">{icon}</div>
    <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
    <p className="text-xs text-slate-500 max-w-sm mt-1 mb-4">{description}</p>
    {action}
  </div>
);

export const LoadingState: React.FC<{ message?: string }> = ({ message = 'Loading operations data...' }) => (
  <div className="flex flex-col items-center justify-center py-16 text-center">
    <Loader2 className="w-8 h-8 text-cyan-800 animate-spin mb-3" />
    <p className="text-xs font-medium text-slate-600">{message}</p>
  </div>
);

export const ErrorState: React.FC<{ title?: string; message: string; onRetry?: () => void }> = ({
  title = 'Operational Error',
  message,
  onRetry,
}) => (
  <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3 text-red-900 text-xs">
    <AlertCircle className="w-5 h-5 text-red-700 shrink-0 mt-0.5" />
    <div className="grow">
      <h4 className="font-semibold">{title}</h4>
      <p className="mt-0.5 text-red-700">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 text-xs font-semibold text-red-800 underline hover:text-red-950"
        >
          Retry action
        </button>
      )}
    </div>
  </div>
);
