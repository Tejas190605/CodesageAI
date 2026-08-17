'use client';

import { useState, useEffect } from 'react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { LoadingSkeleton, ErrorState, EmptyState } from '@/components/ui/States';
import { getInstallations, onboardRepo } from '@/lib/api';
import { Installation } from '@/lib/types';
import { AppWindow, Plus, CheckCircle2, ExternalLink, ShieldCheck, FolderGit2 } from 'lucide-react';

export default function InstallationsPage() {
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Onboarding Form State
  const [owner, setOwner] = useState<string>('');
  const [repoName, setRepoName] = useState<string>('');
  const [selectedInstId, setSelectedInstId] = useState<number | undefined>(undefined);
  const [onboarding, setOnboarding] = useState<boolean>(false);
  const [onboardSuccess, setOnboardSuccess] = useState<string | null>(null);

  const fetchInstallationsList = () => {
    setLoading(true);
    setError(null);
    getInstallations()
      .then((data) => {
        setInstallations(data);
        if (data.length > 0) {
          setSelectedInstId(data[0].installation_id);
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch installations.');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    let isMounted = true;
    getInstallations()
      .then((data) => {
        if (isMounted) {
          setInstallations(data);
          if (data.length > 0) {
            setSelectedInstId(data[0].installation_id);
          }
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to fetch installations.');
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
  }, []);

  const handleOnboardSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!owner.trim() || !repoName.trim()) {
      alert('Please provide repository owner and name.');
      return;
    }
    setOnboarding(true);
    setOnboardSuccess(null);
    try {
      const res = await onboardRepo({
        owner: owner.trim(),
        name: repoName.trim(),
        installation_id: selectedInstId || 0,
      });
      setOnboardSuccess(`Successfully onboarded repository '${res.repository}' to CodeSage AI!`);
      setOwner('');
      setRepoName('');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to onboard repository.');
    } finally {
      setOnboarding(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      <PageHeader
        title="GitHub App & Installation Management"
        description="Manage GitHub App installations, repository authorization tokens, and multi-tenant repository onboarding"
        action={
          <a
            href="https://github.com/apps/codesage-ai/installations/new"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white hover:bg-indigo-500 transition shadow-sm"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Install GitHub App</span>
            <ExternalLink className="h-3 w-3 opacity-70" />
          </a>
        }
      />

      {loading ? (
        <LoadingSkeleton count={3} />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchInstallationsList} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Installations List */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center space-x-2">
              <AppWindow className="h-4 w-4 text-indigo-400" />
              <span>Active GitHub App Installations</span>
            </h3>

            {installations.length === 0 ? (
              <EmptyState
                title="No Active GitHub App Installations"
                description="Install the CodeSage AI GitHub App on your GitHub user or organization account to automatically handle webhooks and review pull requests."
                action={
                  <a
                    href="https://github.com/apps/codesage-ai/installations/new"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition-colors"
                  >
                    <span>Add Installation</span>
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                }
              />
            ) : (
              <div className="space-y-3">
                {installations.map((inst) => (
                  <Card key={inst.id} className="p-4 bg-zinc-900/60 border-zinc-800 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        <ShieldCheck className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-semibold text-zinc-100">@{inst.account_login}</h4>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">
                            ID #{inst.installation_id}
                          </span>
                        </div>
                        <p className="text-xs text-zinc-400 mt-0.5">
                          Type: <strong className="text-zinc-300">{inst.account_type}</strong> • Selection: <span className="text-zinc-300">{inst.repository_selection}</span>
                        </p>
                      </div>
                    </div>

                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Active
                    </span>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Repository Onboarding Form */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-zinc-200 flex items-center space-x-2">
              <FolderGit2 className="h-4 w-4 text-indigo-400" />
              <span>Onboard Repository</span>
            </h3>

            <Card className="p-5 bg-zinc-900/40 border-zinc-800/80 space-y-4">
              <form onSubmit={handleOnboardSubmit} className="space-y-4 text-xs">
                <div>
                  <label className="block text-zinc-400 mb-1 font-medium">Repository Owner</label>
                  <input
                    type="text"
                    placeholder="e.g. Tejas190605"
                    value={owner}
                    onChange={(e) => setOwner(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1 font-medium">Repository Name</label>
                  <input
                    type="text"
                    placeholder="e.g. ResumeIQ"
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1 font-medium">GitHub App Installation</label>
                  <select
                    value={selectedInstId || ''}
                    onChange={(e) => setSelectedInstId(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-100 focus:outline-none focus:border-indigo-500 transition"
                  >
                    {installations.map((inst) => (
                      <option key={inst.id} value={inst.installation_id}>
                        @{inst.account_login} (ID #{inst.installation_id})
                      </option>
                    ))}
                  </select>
                </div>

                {onboardSuccess && (
                  <p className="p-2.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-[11px]">
                    {onboardSuccess}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={onboarding}
                  className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition shadow-sm active:scale-[0.99] disabled:opacity-50"
                >
                  {onboarding ? 'Onboarding...' : 'Onboard Repository'}
                </button>
              </form>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
