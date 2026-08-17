'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { LoadingSkeleton } from '@/components/ui/States';
import { getPolicies, getEffectivePolicy } from '@/lib/api';
import { ReviewPolicyInfo } from '@/lib/types';
import { ShieldCheck, Sliders, CheckCircle2, Lock } from 'lucide-react';

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<ReviewPolicyInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [repository, setRepository] = useState<string>('Tejas190605/ResumeIQ');
  const [effectivePolicy, setEffectivePolicy] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const pList = await getPolicies();
        setPolicies(pList || []);

        const eff = await getEffectivePolicy('Tejas190605', 'ResumeIQ');
        setEffectivePolicy(eff.effective_policy || null);
      } catch (err) {
        console.error('Failed to load policies:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleInspectEffective = async () => {
    const parts = repository.split('/');
    if (parts.length === 2) {
      try {
        const eff = await getEffectivePolicy(parts[0], parts[1]);
        setEffectivePolicy(eff.effective_policy || null);
      } catch (err) {
        console.error('Failed to fetch effective policy:', err);
      }
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col pl-64">
        <PageHeader
          title="Review Policies & Security Rules"
          description="Repository, organization, and system-wide AI code review policy configurations."
        />
        <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
          {/* Policy Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="p-6 bg-slate-900/60 border-slate-800 flex items-center space-x-4">
              <div className="p-3 bg-blue-500/10 text-blue-400 rounded-xl border border-blue-500/20">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400">System Security Rules</p>
                <h3 className="text-xl font-bold text-slate-100">OWASP Top 10 Aligned</h3>
              </div>
            </Card>

            <Card className="p-6 bg-slate-900/60 border-slate-800 flex items-center space-x-4">
              <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400">Deterministic Checks</p>
                <h3 className="text-xl font-bold text-slate-100">Debug & Secret Scanners</h3>
              </div>
            </Card>

            <Card className="p-6 bg-slate-900/60 border-slate-800 flex items-center space-x-4">
              <div className="p-3 bg-purple-500/10 text-purple-400 rounded-xl border border-purple-500/20">
                <Lock className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400">Precedence Order</p>
                <h3 className="text-xl font-bold text-slate-100">Repo → Org → System</h3>
              </div>
            </Card>
          </div>

          {/* Effective Policy Inspector */}
          <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-slate-200">Effective Policy Resolver</h3>
                <p className="text-xs text-slate-400">Inspect resolved rule precedence and path exclusions for a target repository.</p>
              </div>
              <div className="flex items-center space-x-3">
                <input
                  type="text"
                  value={repository}
                  onChange={(e) => setRepository(e.target.value)}
                  className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none"
                  placeholder="owner/repo"
                />
                <button
                  onClick={handleInspectEffective}
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs rounded-lg transition-colors"
                >
                  Resolve Policy
                </button>
              </div>
            </div>

            {effectivePolicy && (
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto">
                <pre>{JSON.stringify(effectivePolicy, null, 2)}</pre>
              </div>
            )}
          </Card>

          {/* Policies Table */}
          {loading ? (
            <LoadingSkeleton count={3} />
          ) : policies.length === 0 ? (
            <Card className="p-8 text-center bg-slate-900/60 border-slate-800 space-y-2">
              <Sliders className="w-8 h-8 text-blue-400 mx-auto" />
              <h3 className="text-base font-medium text-slate-200">System Default Policies Active</h3>
              <p className="text-xs text-slate-400">Repository and organization policy overrides can be configured via .codesage.yml in project root.</p>
            </Card>
          ) : (
            <div className="space-y-4">
              <h3 className="text-base font-semibold text-slate-200">Active Review Policies</h3>
              {policies.map((p) => (
                <div key={p.id} className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-3">
                      <span className="font-semibold text-slate-200">{p.name}</span>
                      <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded text-xs">
                        v{p.version}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{p.description || 'Standard review policy configuration.'}</p>
                  </div>
                  <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded text-xs font-mono">
                    {p.rule_count} Rules Enabled
                  </span>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
