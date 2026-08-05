'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import { PageHeader } from '@/components/layout/PageHeader';
import { MetricCard } from '@/components/ui/MetricCard';
import { LoadingSkeleton } from '@/components/ui/States';
import {
  getAIProviders,
  getPromptTemplates,
  getAIUsage,
  getEvaluations,
  triggerEvaluationRun,
} from '@/lib/api';
import {
  AIProviderInfo,
  PromptTemplateInfo,
  EvaluationRunInfo,
} from '@/lib/types';
import {
  Cpu,
  Zap,
  FileText,
  DollarSign,
  CheckCircle2,
  AlertCircle,
  Play,
  BarChart3,
  Sliders,
} from 'lucide-react';

export default function AISettingsPage() {
  const [activeTab, setActiveTab] = useState<'providers' | 'prompts' | 'usage' | 'evaluations'>('providers');
  const [providers, setProviders] = useState<AIProviderInfo[]>([]);
  const [prompts, setPrompts] = useState<PromptTemplateInfo[]>([]);
  const [usageSummary, setUsageSummary] = useState<{ total_requests: number; total_tokens: number; total_cost_usd: string }>({
    total_requests: 0,
    total_tokens: 0,
    total_cost_usd: '$0.0000',
  });
  const [evaluations, setEvaluations] = useState<EvaluationRunInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggeringEval, setTriggeringEval] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [provRes, promptRes, usageRes, evalRes] = await Promise.all([
          getAIProviders().catch(() => []),
          getPromptTemplates().catch(() => []),
          getAIUsage().catch(() => ({ summary: { total_requests: 0, total_tokens: 0, total_cost_usd: '$0.0000' }, records: [] })),
          getEvaluations().catch(() => []),
        ]);

        setProviders(provRes);
        setPrompts(promptRes);
        setUsageSummary(usageRes.summary);
        setEvaluations(evalRes);
      } catch (err) {
        console.error('Failed to load AI platform data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleRunEvaluation = async () => {
    try {
      setTriggeringEval(true);
      const newRun = await triggerEvaluationRun('Automated Quality Benchmark', 'gemini', 'gemini-2.5-flash');
      setEvaluations((prev) => [newRun, ...prev]);
    } catch (err) {
      console.error('Failed to run evaluation benchmark:', err);
    } finally {
      setTriggeringEval(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col pl-64">
        <PageHeader title="AI Platform Foundation" description="Multi-LLM provider registry, prompt management engine, cost analytics, and benchmark evaluations." />
        <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
          {loading ? (
            <LoadingSkeleton count={4} />
          ) : (
            <>
              {/* Metric Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <MetricCard
                  title="Active LLM Providers"
                  value={providers.filter((p) => p.healthy).length.toString()}
                  description={`${providers.length} registered providers`}
                  icon={Cpu}
                />
                <MetricCard
                  title="Prompt Templates"
                  value={prompts.length.toString()}
                  description="Versioned & validated prompts"
                  icon={FileText}
                />
                <MetricCard
                  title="Total Tokens Processed"
                  value={usageSummary.total_tokens.toLocaleString()}
                  description={`${usageSummary.total_requests} AI inference calls`}
                  icon={Zap}
                />
                <MetricCard
                  title="Estimated API Cost"
                  value={usageSummary.total_cost_usd}
                  description="Cumulative token expenditure"
                  icon={DollarSign}
                />
              </div>

              {/* Dashboard Navigation Tabs */}
              <div className="flex space-x-2 border-b border-slate-800 pb-2">
                <button
                  onClick={() => setActiveTab('providers')}
                  className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'providers'
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  <Cpu className="w-4 h-4" />
                  <span>Providers & Fallback</span>
                </button>
                <button
                  onClick={() => setActiveTab('prompts')}
                  className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'prompts'
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  <span>Prompt Registry</span>
                </button>
                <button
                  onClick={() => setActiveTab('usage')}
                  className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'usage'
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  <BarChart3 className="w-4 h-4" />
                  <span>Usage & Cost Analytics</span>
                </button>
                <button
                  onClick={() => setActiveTab('evaluations')}
                  className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'evaluations'
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  <Sliders className="w-4 h-4" />
                  <span>Evaluations & Benchmarks</span>
                </button>
              </div>

              {/* TAB 1: PROVIDERS */}
              {activeTab === 'providers' && (
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-6">
                  <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-blue-400" />
                    Registered LLM Providers & Health Status
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {providers.map((p) => (
                      <div
                        key={p.name}
                        className="p-5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-4 hover:border-slate-700 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-lg text-slate-200 capitalize">
                            {p.name}
                          </span>
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              p.healthy
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            {p.healthy ? (
                              <>
                                <CheckCircle2 className="w-3 h-3 mr-1" /> Operational
                              </>
                            ) : (
                              <>
                                <AlertCircle className="w-3 h-3 mr-1" /> Unhealthy
                              </>
                            )}
                          </span>
                        </div>

                        <div className="text-xs text-slate-400 space-y-1">
                          <div>Default Model: <span className="text-slate-200 font-mono">{p.default_model}</span></div>
                          <div>Fallback Priority: <span className="text-blue-400 font-semibold">Priority #{p.priority}</span></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 2: PROMPTS */}
              {activeTab === 'prompts' && (
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-6">
                  <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-purple-400" />
                    Central Prompt Registry & Versioning
                  </h2>
                  <div className="space-y-4">
                    {prompts.map((pt) => (
                      <div
                        key={pt.name}
                        className="p-5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <span className="font-semibold text-slate-200">{pt.name}</span>
                            <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded text-xs font-mono">
                              v{pt.version}
                            </span>
                          </div>
                          <span className="text-xs text-emerald-400 font-medium">Active Template</span>
                        </div>
                        <p className="text-xs text-slate-400">{pt.description}</p>
                        <div className="p-3 bg-slate-900 rounded border border-slate-800/80 text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap">
                          {pt.system_prompt}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 3: USAGE */}
              {activeTab === 'usage' && (
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-6">
                  <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-amber-400" />
                    AI Inference Usage & Cost Breakdown
                  </h2>
                  <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 flex justify-between text-sm text-slate-300">
                    <div>Total API Requests: <span className="font-semibold text-slate-100">{usageSummary.total_requests}</span></div>
                    <div>Total Tokens: <span className="font-semibold text-slate-100">{usageSummary.total_tokens}</span></div>
                    <div>Total Expenditure: <span className="font-semibold text-emerald-400">{usageSummary.total_cost_usd}</span></div>
                  </div>
                </div>
              )}

              {/* TAB 4: EVALUATIONS */}
              {activeTab === 'evaluations' && (
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
                      <Sliders className="w-5 h-5 text-emerald-400" />
                      Automated AI Evaluation Benchmarks
                    </h2>
                    <button
                      onClick={handleRunEvaluation}
                      disabled={triggeringEval}
                      className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      <Play className="w-4 h-4" />
                      <span>{triggeringEval ? 'Running Test Suite...' : 'Run Benchmark Evaluation'}</span>
                    </button>
                  </div>

                  <div className="space-y-4">
                    {evaluations.map((ev) => (
                      <div
                        key={ev.id}
                        className="p-5 bg-slate-950/80 border border-slate-800 rounded-xl flex items-center justify-between"
                      >
                        <div>
                          <div className="font-semibold text-slate-200">{ev.run_name}</div>
                          <div className="text-xs text-slate-400 mt-1">
                            Provider: <span className="text-slate-200 capitalize">{ev.provider}</span> | Model: <span className="text-slate-200">{ev.model}</span>
                          </div>
                        </div>

                        <div className="flex items-center space-x-6">
                          <div className="text-right">
                            <div className="text-sm font-bold text-emerald-400">{ev.quality_score}% Score</div>
                            <div className="text-xs text-slate-400">{ev.passed_tests}/{ev.total_tests} Tests Passed</div>
                          </div>
                          <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-xs font-medium capitalize">
                            {ev.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
