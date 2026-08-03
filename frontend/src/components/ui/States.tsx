import React from 'react';
import { AlertCircle, FolderPlus, RefreshCw } from 'lucide-react';
import { Card } from './Card';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <Card className="text-center py-12 px-6 flex flex-col items-center justify-center">
      <div className="p-3 rounded-full bg-zinc-800/80 text-zinc-400 mb-4">
        <FolderPlus className="h-6 w-6 text-indigo-400" />
      </div>
      <h3 className="text-lg font-semibold text-zinc-200">{title}</h3>
      <p className="text-sm text-zinc-400 mt-1 max-w-md mx-auto">{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </Card>
  );
}

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = 'Unable to Load Data', message, onRetry }: ErrorStateProps) {
  return (
    <Card className="border-rose-500/20 bg-rose-500/5 p-6 text-center flex flex-col items-center">
      <div className="p-3 rounded-full bg-rose-500/10 text-rose-400 mb-3">
        <AlertCircle className="h-6 w-6" />
      </div>
      <h3 className="text-base font-semibold text-rose-200">{title}</h3>
      <p className="text-sm text-zinc-400 mt-1 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-zinc-200 transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Retry Request</span>
        </button>
      )}
    </Card>
  );
}

export function LoadingSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="h-20 rounded-xl bg-zinc-900/60 border border-zinc-800/80 animate-pulse p-4 flex flex-col justify-between"
        >
          <div className="h-4 bg-zinc-800 rounded w-1/3" />
          <div className="h-3 bg-zinc-800/60 rounded w-2/3" />
        </div>
      ))}
    </div>
  );
}
