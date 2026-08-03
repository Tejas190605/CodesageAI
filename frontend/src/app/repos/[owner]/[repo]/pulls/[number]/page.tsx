'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import { getPullRequest, getPullRequestReview } from '@/lib/api';
import { PullRequestDetail, PullRequestReviewResponse } from '@/lib/types';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { ScoreBadge, StatusBadge } from '@/components/ui/Badges';
import { MarkdownViewer } from '@/components/ui/MarkdownViewer';
import { EmptyState, ErrorState, LoadingSkeleton } from '@/components/ui/States';
import {
  GitBranch,
  ExternalLink,
  ArrowLeft,
  FileCode,
  PlusCircle,
  MinusCircle,
  MessageSquare,
  Bot,
  ShieldAlert,
} from 'lucide-react';

interface PageProps {
  params: Promise<{ owner: string; repo: string; number: string }>;
}

export default function PullRequestReviewPage({ params }: PageProps) {
  const { owner, repo, number: rawNumber } = use(params);
  const prNumber = parseInt(rawNumber, 10);

  const [prDetail, setPrDetail] = useState<PullRequestDetail | null>(null);
  const [reviewData, setReviewData] = useState<PullRequestReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      getPullRequest(owner, repo, prNumber),
      getPullRequestReview(owner, repo, prNumber),
    ])
      .then(([prRes, reviewRes]) => {
        if (isMounted) {
          setPrDetail(prRes);
          setReviewData(reviewRes);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load pull request review details.');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [owner, repo, prNumber, reloadToken]);

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setReloadToken((prev) => prev + 1);
  };

  if (loading) {
    return (
      <div>
        <PageHeader title={`PR #${prNumber}`} description="Loading AI review..." />
        <LoadingSkeleton count={3} />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="mb-4">
          <Link href={`/repos/${owner}/${repo}`} className="text-xs text-indigo-400 flex items-center space-x-1">
            <ArrowLeft className="h-3 w-3" />
            <span>Back to Repository</span>
          </Link>
        </div>
        <ErrorState message={error} onRetry={handleRetry} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <div>
        <Link
          href={`/repos/${owner}/${repo}`}
          className="inline-flex items-center space-x-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to {owner}/{repo}</span>
        </Link>
      </div>

      {prDetail && (
        <PageHeader
          title={`${prDetail.title} (#${prDetail.number})`}
          description={`Opened by @${prDetail.author} • ${prDetail.head_branch} → ${prDetail.base_branch}`}
          action={
            <div className="flex items-center space-x-3">
              <StatusBadge state={prDetail.state} draft={prDetail.draft} />
              <a
                href={prDetail.html_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs text-zinc-200 hover:border-zinc-700 transition-colors"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                <span>View PR on GitHub</span>
              </a>
            </div>
          }
        />
      )}

      {/* Stats Summary Bar */}
      {prDetail && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <Card className="p-3 text-center">
            <div className="flex items-center justify-center space-x-1 text-zinc-400 text-xs">
              <FileCode className="h-3.5 w-3.5 text-indigo-400" />
              <span>Files Changed</span>
            </div>
            <p className="text-lg font-bold text-zinc-100 mt-1">{prDetail.changed_files}</p>
          </Card>

          <Card className="p-3 text-center">
            <div className="flex items-center justify-center space-x-1 text-zinc-400 text-xs">
              <PlusCircle className="h-3.5 w-3.5 text-emerald-400" />
              <span>Additions</span>
            </div>
            <p className="text-lg font-bold text-emerald-400 mt-1">+{prDetail.additions}</p>
          </Card>

          <Card className="p-3 text-center">
            <div className="flex items-center justify-center space-x-1 text-zinc-400 text-xs">
              <MinusCircle className="h-3.5 w-3.5 text-rose-400" />
              <span>Deletions</span>
            </div>
            <p className="text-lg font-bold text-rose-400 mt-1">-{prDetail.deletions}</p>
          </Card>

          <Card className="p-3 text-center">
            <div className="flex items-center justify-center space-x-1 text-zinc-400 text-xs">
              <GitBranch className="h-3.5 w-3.5 text-zinc-400" />
              <span>Commits</span>
            </div>
            <p className="text-lg font-bold text-zinc-100 mt-1">{prDetail.commits}</p>
          </Card>

          <Card className="p-3 text-center col-span-2 sm:col-span-1">
            <div className="flex items-center justify-center space-x-1 text-zinc-400 text-xs">
              <MessageSquare className="h-3.5 w-3.5 text-indigo-400" />
              <span>Comments</span>
            </div>
            <p className="text-lg font-bold text-zinc-100 mt-1">{prDetail.comments}</p>
          </Card>
        </div>
      )}

      {/* AI Review Details Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-zinc-100 flex items-center space-x-2">
            <Bot className="h-5 w-5 text-indigo-400" />
            <span>CodeSage AI Review Findings</span>
          </h2>
          {reviewData?.reviewed && reviewData.latest_review?.overall_rating !== undefined && (
            <div className="flex items-center space-x-2">
              <span className="text-xs text-zinc-400 font-medium">Quality Rating:</span>
              <ScoreBadge score={reviewData.latest_review.overall_rating} size="lg" />
            </div>
          )}
        </div>

        {!reviewData || !reviewData.reviewed || !reviewData.latest_review ? (
          <EmptyState
            title="No CodeSage Review Recorded"
            description="No CodeSage AI review has been posted for this pull request yet. Webhook events (opened, synchronize) automatically trigger Gemini AI analysis."
          />
        ) : (
          <Card className="space-y-6 p-6">
            {/* Header info */}
            <div className="flex flex-wrap items-center justify-between pb-4 border-b border-zinc-800/80 gap-3 text-xs text-zinc-400">
              <div className="flex items-center space-x-3">
                <span className="flex items-center space-x-1">
                  <ShieldAlert className="h-4 w-4 text-emerald-400" />
                  <span>AI Scanned & Verified</span>
                </span>
                <span>•</span>
                <span>Review History: <strong>{reviewData.review_count} comment(s)</strong></span>
              </div>
              <div className="text-zinc-500">
                Posted: {new Date(reviewData.latest_review.created_at).toLocaleString()}
              </div>
            </div>

            {/* Markdown Body */}
            <div className="prose prose-invert max-w-none">
              <MarkdownViewer content={reviewData.latest_review.markdown} />
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
