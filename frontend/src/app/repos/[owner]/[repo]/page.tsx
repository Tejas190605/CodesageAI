'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import { getRepository } from '@/lib/api';
import { RepositorySummary, PullRequestSummary } from '@/lib/types';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { PullRequestRow } from '@/components/ui/PullRequestRow';
import { EmptyState, ErrorState, LoadingSkeleton } from '@/components/ui/States';
import { GitBranch, GitPullRequest, ExternalLink, ArrowLeft } from 'lucide-react';

interface PageProps {
  params: Promise<{ owner: string; repo: string }>;
}

export default function RepositoryDetailPage({ params }: PageProps) {
  const { owner, repo } = use(params);

  const [repoInfo, setRepoInfo] = useState<RepositorySummary | null>(null);
  const [pulls, setPulls] = useState<PullRequestSummary[]>([]);
  const [filterState, setFilterState] = useState<'all' | 'open' | 'closed'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let isMounted = true;
    getRepository(owner, repo)
      .then((res) => {
        if (isMounted) {
          setRepoInfo(res.repository);
          setPulls(res.pull_requests);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load repository detail.');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [owner, repo, reloadToken]);

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setReloadToken((prev) => prev + 1);
  };

  const filteredPulls = pulls.filter((pr) => {
    if (filterState === 'open') return pr.state === 'open';
    if (filterState === 'closed') return pr.state === 'closed';
    return true;
  });

  if (loading) {
    return (
      <div>
        <PageHeader title={`${owner}/${repo}`} description="Loading pull requests..." />
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="mb-4">
          <Link href="/repos" className="text-xs text-indigo-400 flex items-center space-x-1">
            <ArrowLeft className="h-3 w-3" />
            <span>Back to Repositories</span>
          </Link>
        </div>
        <ErrorState message={error} onRetry={handleRetry} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb Navigation */}
      <div>
        <Link
          href="/repos"
          className="inline-flex items-center space-x-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Repositories</span>
        </Link>
      </div>

      <PageHeader
        title={`${owner}/${repo}`}
        description={repoInfo?.description || 'Monitored repository pull requests'}
        action={
          repoInfo && (
            <a
              href={repoInfo.html_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs text-zinc-200 hover:border-zinc-700 transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              <span>View on GitHub</span>
            </a>
          )
        }
      />

      {/* Repo Quick Info Card */}
      {repoInfo && (
        <Card className="flex flex-wrap items-center justify-between gap-4 text-xs text-zinc-400">
          <div className="flex items-center space-x-6">
            <span className="flex items-center space-x-1.5">
              <GitBranch className="h-4 w-4 text-indigo-400" />
              <span className="font-mono text-zinc-200">{repoInfo.default_branch}</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <GitPullRequest className="h-4 w-4 text-emerald-400" />
              <span className="font-semibold text-zinc-200">{repoInfo.open_pull_requests}</span>
              <span>Open PRs</span>
            </span>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center bg-zinc-950 p-1 rounded-lg border border-zinc-800">
            {(['all', 'open', 'closed'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setFilterState(st)}
                className={`px-3 py-1 rounded-md text-xs capitalize font-medium transition-colors ${
                  filterState === st
                    ? 'bg-zinc-800 text-indigo-400'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Pull Requests List */}
      <div className="space-y-3">
        {filteredPulls.length === 0 ? (
          <EmptyState
            title="No Pull Requests Found"
            description={`No ${filterState !== 'all' ? filterState : ''} pull requests found for ${owner}/${repo}.`}
          />
        ) : (
          filteredPulls.map((pr) => (
            <PullRequestRow key={pr.number} owner={owner} repo={repo} pr={pr} />
          ))
        )}
      </div>
    </div>
  );
}
