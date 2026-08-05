'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { LoadingSkeleton } from '@/components/ui/States';
import {
  getAnalyticsOverview,
  getReviewAnalytics,
  getFindingAnalytics,
  getAIUsageAnalytics,
  getJobAnalytics,
} from '@/lib/api';
import {
  AnalyticsOverviewInfo,
  ReviewAnalyticsInfo,
  FindingAnalyticsInfo,
  AIUsageAnalyticsInfo,
  JobAnalyticsInfo,
} from '@/lib/types';
import { BarChart3, CheckCircle2, AlertTriangle, ShieldCheck, DollarSign, Activity, GitBranch } from 'lucide-react';

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverviewInfo | null>(null);
  const [reviews, setReviews] = useState<ReviewAnalyticsInfo | null>(null);
  const [findings, setFindings] = useState<FindingAnalyticsInfo | null>(null);
  const [aiUsage, setAiUsage] = useState<AIUsageAnalyticsInfo | null>(null);
  const [jobs, setJobs] = useState<JobAnalyticsInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadAllAnalytics() {
      try {
        setLoading(true);
        const [ov, rev, find, ai, jb] = await Promise.all([
          getAnalyticsOverview(),
          getReviewAnalytics(),
          getFindingAnalytics(),
          getAIUsageAnalytics(),
          getJobAnalytics(),
        ]);
        setOverview(ov);
        setReviews(rev);
        setFindings(find);
        setAiUsage(ai);
        setJobs(jb);
      } catch (err) {
        console.error('Failed to load analytics:', err);
      } finally {
        setLoading(false);
      }
    }
    loadAllAnalytics();
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col pl-64">
        <PageHeader
          title="Project Insights & Engineering Analytics"
          description="Real-time analytics for review activity, finding severities, AI token costs, and job queue metrics."
        />
        <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
          {loading ? (
            <LoadingSkeleton count={4} />
          ) : (
            <>
              {/* Overview Metrics Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Indexed Repositories</span>
                    <GitBranch className="w-4 h-4 text-blue-400" />
                  </div>
                  <h3 className="text-3xl font-bold text-slate-100">{overview?.total_repositories || 0}</h3>
                </Card>

                <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Pull Requests Processed</span>
                    <BarChart3 className="w-4 h-4 text-purple-400" />
                  </div>
                  <h3 className="text-3xl font-bold text-slate-100">{overview?.total_pull_requests || 0}</h3>
                </Card>

                <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Code Reviews Executed</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div className="flex items-baseline justify-between">
                    <h3 className="text-3xl font-bold text-slate-100">{overview?.total_reviews || 0}</h3>
                    <span className="text-xs font-mono text-emerald-400">{reviews?.approval_rate || 100}% Approval</span>
                  </div>
                </Card>

                <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                    <span>Policy Findings</span>
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                  </div>
                  <h3 className="text-3xl font-bold text-slate-100">{overview?.total_findings || 0}</h3>
                </Card>
              </div>

              {/* Finding Severities & Review Reliability */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-4">
                  <h3 className="text-base font-semibold text-slate-200 flex items-center space-x-2">
                    <ShieldCheck className="w-5 h-5 text-red-400" />
                    <span>Findings by Severity Level</span>
                  </h3>
                  <div className="space-y-3 pt-2">
                    <div className="flex items-center justify-between text-xs font-medium text-slate-300">
                      <span className="text-red-400 font-bold">🚨 Critical</span>
                      <span className="font-mono px-2 py-0.5 bg-red-500/10 border border-red-500/20 rounded">
                        {findings?.by_severity.critical || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs font-medium text-slate-300">
                      <span className="text-amber-400 font-bold">⚠️ High</span>
                      <span className="font-mono px-2 py-0.5 bg-amber-500/10 border border-amber-500/20 rounded">
                        {findings?.by_severity.high || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs font-medium text-slate-300">
                      <span className="text-yellow-300 font-bold">🟡 Medium</span>
                      <span className="font-mono px-2 py-0.5 bg-yellow-500/10 border border-yellow-500/20 rounded">
                        {findings?.by_severity.medium || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs font-medium text-slate-300">
                      <span className="text-blue-400 font-bold">🔹 Low / Info</span>
                      <span className="font-mono px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 rounded">
                        {(findings?.by_severity.low || 0) + (findings?.by_severity.info || 0)}
                      </span>
                    </div>
                  </div>
                </Card>

                <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-4">
                  <h3 className="text-base font-semibold text-slate-200 flex items-center space-x-2">
                    <Activity className="w-5 h-5 text-emerald-400" />
                    <span>Job Queue Reliability</span>
                  </h3>
                  <div className="space-y-3 pt-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">Queue Success Rate</span>
                      <span className="text-emerald-400 font-bold font-mono">{jobs?.success_rate_percent || 100}%</span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-2 border border-slate-800 overflow-hidden">
                      <div
                        className="bg-emerald-500 h-full transition-all duration-500"
                        style={{ width: `${jobs?.success_rate_percent || 100}%` }}
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-2 pt-2 text-center text-xs font-mono">
                      <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                        <span className="text-slate-400 block text-[10px]">Completed</span>
                        <span className="text-slate-100 font-bold">{jobs?.completed || 0}</span>
                      </div>
                      <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                        <span className="text-slate-400 block text-[10px]">Queued</span>
                        <span className="text-slate-100 font-bold">{jobs?.queued || 0}</span>
                      </div>
                      <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                        <span className="text-slate-400 block text-[10px]">Failed</span>
                        <span className="text-red-400 font-bold">{jobs?.failed || 0}</span>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>

              {/* AI Usage & Cost Analytics */}
              <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-slate-200 flex items-center space-x-2">
                    <DollarSign className="w-5 h-5 text-emerald-400" />
                    <span>AI Provider Cost & Token Consumption</span>
                  </h3>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 block">Total Estimated Cost</span>
                    <span className="text-xl font-bold font-mono text-emerald-400">${aiUsage?.total_cost_usd || '0.0000'}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                    <span className="text-xs text-slate-400">Total Tokens Processed</span>
                    <p className="text-2xl font-bold font-mono text-slate-100">
                      {aiUsage?.total_tokens.toLocaleString() || 0}
                    </p>
                  </div>

                  <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                    <span className="text-xs text-slate-400">Total LLM Requests</span>
                    <p className="text-2xl font-bold font-mono text-slate-100">
                      {aiUsage?.total_requests || 0}
                    </p>
                  </div>
                </div>
              </Card>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
