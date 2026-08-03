import Link from 'next/link';
import { PullRequestSummary } from '@/lib/types';
import { StatusBadge } from './Badges';
import { GitPullRequest, GitBranch, Clock, User } from 'lucide-react';

interface PullRequestRowProps {
  owner: string;
  repo: string;
  pr: PullRequestSummary;
}

export function PullRequestRow({ owner, repo, pr }: PullRequestRowProps) {
  const formattedDate = pr.updated_at
    ? new Date(pr.updated_at).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : null;

  return (
    <Link
      href={`/repos/${owner}/${repo}/pulls/${pr.number}`}
      className="block p-4 rounded-xl border border-zinc-800/80 bg-zinc-900/40 hover:bg-zinc-900/90 hover:border-zinc-700/80 transition-colors"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-start space-x-3 min-w-0">
          <div className="p-2 rounded-lg bg-zinc-800/80 text-indigo-400 shrink-0 mt-0.5">
            <GitPullRequest className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center space-x-2 flex-wrap gap-y-1">
              <span className="font-semibold text-sm text-zinc-100 hover:text-indigo-400 transition-colors truncate">
                {pr.title}
              </span>
              <span className="text-xs text-zinc-500 font-mono">#{pr.number}</span>
              <StatusBadge state={pr.state} draft={pr.draft} />
            </div>

            <div className="flex items-center space-x-4 text-xs text-zinc-400 mt-1.5 flex-wrap gap-y-1">
              <span className="flex items-center space-x-1">
                <User className="h-3 w-3 text-zinc-500" />
                <span>{pr.author}</span>
              </span>
              <span className="flex items-center space-x-1 font-mono text-[11px] text-zinc-400">
                <GitBranch className="h-3 w-3 text-zinc-500" />
                <span>{pr.head_branch}</span>
                <span>→</span>
                <span>{pr.base_branch}</span>
              </span>
              {formattedDate && (
                <span className="flex items-center space-x-1 text-zinc-500">
                  <Clock className="h-3 w-3" />
                  <span>{formattedDate}</span>
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}
