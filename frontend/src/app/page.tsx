'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getDashboard } from '@/lib/api';
import { DashboardSummary } from '@/lib/types';
import { PageHeader } from '@/components/layout/PageHeader';
import { MetricCard } from '@/components/ui/MetricCard';
import { PullRequestRow } from '@/components/ui/PullRequestRow';
import { EmptyState, ErrorState, LoadingSkeleton } from '@/components/ui/States';
import { Card } from '@/components/ui/Card';
import { GitBranch, GitPullRequest, ShieldCheck, Star, Bot, ArrowRight, Server } from 'lucide-react';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let isMounted = true;
    getDashboard()
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to connect to CodeSage backend.');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [reloadToken]);

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setReloadToken((prev) => prev + 1);
  };

  if (loading) {
    return (
      <div>
        <PageHeader title="Dashboard" description="Loading code review intelligence..." />
        <LoadingSkeleton count={4} />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <PageHeader title="Dashboard" description="System Overview" />
        <ErrorState message={error} onRetry={handleRetry} />
      </div>
    );
  }

  if (!data || data.repositories_count === 0) {
    return (
      <div>
        <PageHeader title="Dashboard" description="AI Code Review Intelligence" />
        <EmptyState
          title="No Repositories Monitored"
          description="To start monitoring pull requests, add repository identifiers to CODESAGE_REPOSITORIES in your backend .env file."
          action={
            <Link
              href="/settings"
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition-colors"
            >
              <span>View Setup Instructions</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="AI-powered code review intelligence and system code health."
      />

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Monitored Repositories"
          value={data.repositories_count}
          icon={GitBranch}
          badgeText="Active"
          badgeColor="indigo"
        />
        <MetricCard
          title="Open Pull Requests"
          value={data.open_pull_requests}
          icon={GitPullRequest}
          badgeText="Live"
          badgeColor="emerald"
        />
        <MetricCard
          title="Reviewed PRs"
          value={data.reviewed_pull_requests}
          icon={ShieldCheck}
          badgeText="AI Scanned"
          badgeColor="indigo"
        />
        <MetricCard
          title="Average Score"
          value={data.average_score ? `${data.average_score}/10` : '—'}
          icon={Star}
          badgeText="Quality"
          badgeColor={data.average_score && data.average_score >= 8 ? 'emerald' : 'amber'}
        />
      </div>

      {/* Main Grid: Recent PRs & Architecture Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Pull Requests (2 Columns) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-zinc-100 flex items-center space-x-2">
              <GitPullRequest className="h-4 w-4 text-indigo-400" />
              <span>Recent Pull Requests</span>
            </h2>
            <Link
              href="/repos"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center space-x-1"
            >
              <span>View Repositories</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {data.recent_pull_requests.length === 0 ? (
            <Card className="text-center py-8 text-zinc-500 text-xs">
              No recent pull requests found across monitored repositories.
            </Card>
          ) : (
            <div className="space-y-3">
              {data.recent_pull_requests.map((pr) => (
                <PullRequestRow
                  key={pr.number}
                  owner="Tejas190605"
                  repo="codexproj"
                  pr={pr}
                />
              ))}
            </div>
          )}
        </div>

        {/* System Architecture & Status Card (1 Column) */}
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-zinc-100 flex items-center space-x-2">
            <Server className="h-4 w-4 text-emerald-400" />
            <span>Architecture & Status</span>
          </h2>
          <Card className="space-y-4">
            <div className="flex items-center space-x-3 pb-3 border-b border-zinc-800">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-xs font-semibold text-zinc-200">Gemini 2.5 Structured Review Engine</h3>
                <p className="text-[11px] text-zinc-400">FastAPI Async Webhook Processing</p>
              </div>
            </div>

            <div className="space-y-2 text-xs text-zinc-400">
              <div className="flex justify-between py-1 border-b border-zinc-800/50">
                <span>Webhook Verification</span>
                <span className="text-emerald-400 font-mono font-medium">HMAC-SHA256</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800/50">
                <span>Diff Truncation</span>
                <span className="text-zinc-300 font-mono">12k chars/file</span>
              </div>
              <div className="flex justify-between py-1 border-b border-zinc-800/50">
                <span>Structured Output</span>
                <span className="text-indigo-400 font-mono font-medium">Pydantic Schema</span>
              </div>
              <div className="flex justify-between py-1">
                <span>Data Strategy</span>
                <span className="text-zinc-300 font-mono">GitHub REST API</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
