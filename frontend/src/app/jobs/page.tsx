'use client';

import { useState, useEffect, useCallback } from 'react';
import { PageHeader } from '@/components/layout/PageHeader';
import { MetricCard } from '@/components/ui/MetricCard';
import { LoadingSkeleton, ErrorState, EmptyState } from '@/components/ui/States';
import { getJobs, getWorkerHealth, retryJob, cancelJob } from '@/lib/api';
import { ReviewJob, WorkerHealthResponse } from '@/lib/types';
import {
  PlayCircle,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Skull,
  Clock,
  RefreshCw,
  Server,
} from 'lucide-react';

const STATUS_TABS = [
  { id: 'all', label: 'All Jobs' },
  { id: 'queued', label: 'Queued' },
  { id: 'running', label: 'Running' },
  { id: 'completed', label: 'Completed' },
  { id: 'failed', label: 'Failed' },
  { id: 'retry', label: 'Retry' },
  { id: 'dead_letter', label: 'Dead-Letter' },
];

export default function JobsPage() {
  const [activeTab, setActiveTab] = useState<string>('all');
  const [jobs, setJobs] = useState<ReviewJob[]>([]);
  const [health, setHealth] = useState<WorkerHealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionJobId, setActionJobId] = useState<string | null>(null);

  const reloadData = useCallback(async () => {
    setRefreshing(true);
    try {
      setError(null);
      const [jobsData, healthData] = await Promise.all([
        getJobs(activeTab),
        getWorkerHealth(),
      ]);
      setJobs(jobsData);
      setHealth(healthData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch job queue data.');
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    let isMounted = true;
    Promise.all([getJobs(activeTab), getWorkerHealth()])
      .then(([jobsData, healthData]) => {
        if (isMounted) {
          setJobs(jobsData);
          setHealth(healthData);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to fetch job queue data.');
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [activeTab]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      reloadData();
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, reloadData]);

  const handleRetry = async (jobId: string) => {
    setActionJobId(jobId);
    try {
      await retryJob(jobId);
      await reloadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to retry job.');
    } finally {
      setActionJobId(null);
    }
  };

  const handleCancel = async (jobId: string) => {
    setActionJobId(jobId);
    try {
      await cancelJob(jobId);
      await reloadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to cancel job.');
    } finally {
      setActionJobId(null);
    }
  };

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case 'queued':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="w-3.5 h-3.5" /> Queued
          </span>
        );
      case 'running':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse">
            <PlayCircle className="w-3.5 h-3.5" /> Running
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" /> Completed
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" /> Failed
          </span>
        );
      case 'retry':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <RotateCcw className="w-3.5 h-3.5" /> Retry
          </span>
        );
      case 'dead_letter':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-zinc-800 text-rose-300 border border-rose-900/50">
            <Skull className="w-3.5 h-3.5" /> Dead-Letter
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Background Job Queue"
        description="Real-time Redis worker queue, execution status, retry policies, and dead-letter monitoring"
        action={
          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-2 text-xs text-zinc-400 bg-zinc-900 px-3 py-1.5 rounded-lg border border-zinc-800 cursor-pointer hover:border-zinc-700 transition">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded bg-zinc-950 border-zinc-800 text-indigo-600 focus:ring-0"
              />
              <span>Auto-refresh (5s)</span>
            </label>
            <button
              onClick={() => reloadData()}
              disabled={refreshing}
              className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-50 transition shadow-sm"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        }
      />

      {loading ? (
        <LoadingSkeleton count={4} />
      ) : error ? (
        <ErrorState message={error} onRetry={() => reloadData()} />
      ) : (
        <>
          {/* Worker Queue Metrics Breakdown */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <MetricCard
              title="Queued"
              value={health?.metrics.queued ?? 0}
              icon={Clock}
              description="Pending execution"
            />
            <MetricCard
              title="Running"
              value={health?.metrics.running ?? 0}
              icon={PlayCircle}
              description="Active worker threads"
            />
            <MetricCard
              title="Completed"
              value={health?.metrics.completed ?? 0}
              icon={CheckCircle2}
              description="Successful AI reviews"
            />
            <MetricCard
              title="Failed"
              value={health?.metrics.failed ?? 0}
              icon={XCircle}
              description="Review errors"
            />
            <MetricCard
              title="Retry"
              value={health?.metrics.retry ?? 0}
              icon={RotateCcw}
              description="Exponential backoff"
            />
            <MetricCard
              title="Dead-Letter"
              value={health?.metrics.dead_letter ?? 0}
              icon={Skull}
              description="Exceeded max retries"
            />
          </div>

          {/* Status Filter Tabs */}
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <div className="flex items-center space-x-1 overflow-x-auto">
              {STATUS_TABS.map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-zinc-800 text-indigo-400 border border-zinc-700'
                        : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                    }`}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </div>
            <div className="flex items-center space-x-2 text-xs text-zinc-400">
              <Server className="h-3.5 w-3.5 text-zinc-500" />
              <span>
                Concurrency: <strong className="text-zinc-200">{health?.concurrency_limit ?? 5}</strong>
              </span>
            </div>
          </div>

          {/* Jobs Table */}
          {jobs.length === 0 ? (
            <EmptyState
              title="No Jobs Found"
              description={`There are currently no background review jobs matching status '${activeTab}'.`}
            />
          ) : (
            <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-zinc-300">
                  <thead className="bg-zinc-950/80 text-zinc-400 uppercase tracking-wider text-[11px] border-b border-zinc-800">
                    <tr>
                      <th className="px-4 py-3">Job ID</th>
                      <th className="px-4 py-3">Repository & PR</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Attempts</th>
                      <th className="px-4 py-3">Created</th>
                      <th className="px-4 py-3">Failure Reason</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60">
                    {jobs.map((job) => (
                      <tr key={job.job_id} className="hover:bg-zinc-800/30 transition">
                        <td className="px-4 py-3 font-mono text-zinc-200 font-medium">
                          {job.job_id}
                        </td>
                        <td className="px-4 py-3 font-medium text-zinc-100">
                          {job.repository} <span className="text-indigo-400">#{job.pr_number}</span>
                          {job.pr_title && (
                            <p className="text-[11px] text-zinc-400 font-normal truncate max-w-xs">
                              {job.pr_title}
                            </p>
                          )}
                        </td>
                        <td className="px-4 py-3">{renderStatusBadge(job.status)}</td>
                        <td className="px-4 py-3 font-mono text-zinc-400">
                          {job.attempts} / {job.max_retries}
                        </td>
                        <td className="px-4 py-3 text-zinc-400">
                          {job.created_at ? new Date(job.created_at).toLocaleTimeString() : 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-rose-400/90 font-mono text-[11px] max-w-xs truncate">
                          {job.failure_reason || '—'}
                        </td>
                        <td className="px-4 py-3 text-right space-x-2">
                          {['failed', 'dead_letter', 'retry', 'cancelled'].includes(job.status) && (
                            <button
                              onClick={() => handleRetry(job.job_id)}
                              disabled={actionJobId === job.job_id}
                              className="px-2.5 py-1 rounded bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/40 text-[11px] font-medium transition"
                            >
                              Retry
                            </button>
                          )}
                          {['queued', 'retry'].includes(job.status) && (
                            <button
                              onClick={() => handleCancel(job.job_id)}
                              disabled={actionJobId === job.job_id}
                              className="px-2.5 py-1 rounded bg-rose-600/20 text-rose-300 border border-rose-500/30 hover:bg-rose-600/40 text-[11px] font-medium transition"
                            >
                              Cancel
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
