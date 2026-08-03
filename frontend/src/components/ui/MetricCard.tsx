import React from 'react';
import { Card } from './Card';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
  badgeText?: string;
  badgeColor?: 'emerald' | 'indigo' | 'amber' | 'rose';
}

export function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  badgeText,
  badgeColor = 'indigo',
}: MetricCardProps) {
  const badgeClasses = {
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    indigo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  }[badgeColor];

  return (
    <Card className="relative overflow-hidden">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">{title}</span>
        <div className="p-2 rounded-lg bg-zinc-800/80 text-zinc-300">
          <Icon className="h-4 w-4 text-indigo-400" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-3xl font-bold text-zinc-100 tracking-tight">{value}</span>
        {badgeText && (
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${badgeClasses}`}>
            {badgeText}
          </span>
        )}
      </div>
      {description && <p className="text-xs text-zinc-500 mt-2">{description}</p>}
    </Card>
  );
}
