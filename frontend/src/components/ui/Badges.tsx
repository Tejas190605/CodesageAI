import React from 'react';

interface ScoreBadgeProps {
  score: number | null | undefined;
  size?: 'sm' | 'md' | 'lg';
}

export function ScoreBadge({ score, size = 'md' }: ScoreBadgeProps) {
  if (score === null || score === undefined) {
    return <span className="text-xs text-zinc-500 font-mono">—</span>;
  }

  let colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
  if (score < 5) {
    colorClasses = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
  } else if (score < 8) {
    colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1 font-semibold',
    lg: 'text-base px-3.5 py-1.5 font-bold',
  }[size];

  return (
    <span className={`inline-flex items-center rounded-lg border font-mono tracking-tight ${colorClasses} ${sizeClasses}`}>
      {score}/10
    </span>
  );
}

interface StatusBadgeProps {
  state: string;
  draft?: boolean;
}

export function StatusBadge({ state, draft }: StatusBadgeProps) {
  if (draft) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
        Draft
      </span>
    );
  }

  if (state === 'open') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        Open
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
      Closed
    </span>
  );
}
