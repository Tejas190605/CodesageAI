'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getRepositories } from '@/lib/api';
import { RepositorySummary } from '@/lib/types';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingSkeleton } from '@/components/ui/States';
import { GitBranch, GitPullRequest, Search, Lock, Globe, ExternalLink, ArrowRight } from 'lucide-react';

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<RepositorySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let isMounted = true;
    getRepositories()
      .then((res) => {
        if (isMounted) {
          setRepos(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to fetch repositories.');
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

  const filteredRepos = repos.filter(
    (r) =>
      r.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.description && r.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (loading) {
    return (
      <div>
        <PageHeader title="Repositories" description="Loading monitored repositories..." />
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <PageHeader title="Repositories" description="Monitored Repositories" />
        <ErrorState message={error} onRetry={handleRetry} />
      </div>
    );
  }

  if (repos.length === 0) {
    return (
      <div>
        <PageHeader title="Repositories" description="Monitored GitHub Repositories" />
        <EmptyState
          title="No Repositories Configured"
          description="Configure CODESAGE_REPOSITORIES in backend .env to start monitoring GitHub repositories."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Repositories"
        description="Monitored GitHub repositories with open pull request counts."
        action={
          <div className="relative w-full sm:w-64">
            <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              placeholder="Filter repositories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredRepos.map((repo) => (
          <Card key={repo.full_name} className="flex flex-col justify-between hover:border-indigo-500/50">
            <div>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <GitBranch className="h-4 w-4 text-indigo-400" />
                  <Link
                    href={`/repos/${repo.owner}/${repo.name}`}
                    className="font-bold text-base text-zinc-100 hover:text-indigo-400 transition-colors"
                  >
                    {repo.full_name}
                  </Link>
                </div>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
                  {repo.private ? <Lock className="h-3 w-3 mr-1 text-amber-400" /> : <Globe className="h-3 w-3 mr-1 text-emerald-400" />}
                  {repo.private ? 'Private' : 'Public'}
                </span>
              </div>

              {repo.description ? (
                <p className="text-xs text-zinc-400 mt-2 line-clamp-2">{repo.description}</p>
              ) : (
                <p className="text-xs text-zinc-600 italic mt-2">No description provided.</p>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-zinc-800/80 flex items-center justify-between text-xs text-zinc-400">
              <div className="flex items-center space-x-4">
                <span className="flex items-center space-x-1">
                  <GitPullRequest className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="font-semibold text-zinc-200">{repo.open_pull_requests}</span>
                  <span>Open PRs</span>
                </span>
                <span className="text-zinc-500 font-mono text-[11px]">
                  branch: {repo.default_branch}
                </span>
              </div>

              <div className="flex items-center space-x-3">
                <a
                  href={repo.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-zinc-500 hover:text-zinc-300 p-1"
                  title="Open on GitHub"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
                <Link
                  href={`/repos/${repo.owner}/${repo.name}`}
                  className="inline-flex items-center space-x-1 text-indigo-400 hover:text-indigo-300 font-semibold text-xs"
                >
                  <span>View PRs</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
