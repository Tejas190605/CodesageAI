'use client';

import { useState } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { LoadingSkeleton, EmptyState } from '@/components/ui/States';
import { searchCode } from '@/lib/api';
import { SearchResultChunk } from '@/lib/types';
import { Search, Code2, Sparkles, Filter } from 'lucide-react';

export default function CodeSearchPage() {
  const [repository, setRepository] = useState<string>('Tejas190605/ResumeIQ');
  const [query, setQuery] = useState<string>('');
  const [language, setLanguage] = useState<string>('');
  const [results, setResults] = useState<SearchResultChunk[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [searched, setSearched] = useState<boolean>(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !repository.trim()) return;

    try {
      setLoading(true);
      setSearched(true);
      const res = await searchCode(repository.trim(), query.trim(), 10, language || null);
      setResults(res.results || []);
    } catch (err) {
      console.error('Code search error:', err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col pl-64">
        <PageHeader
          title="Repository Code Search & Intelligence"
          description="Hybrid vector semantic and exact lexical code search across indexed repositories."
        />
        <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
          {/* Search Form */}
          <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-4">
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="w-full md:w-1/3">
                  <label className="block text-xs font-medium text-slate-400 mb-1">Target Repository</label>
                  <input
                    type="text"
                    value={repository}
                    onChange={(e) => setRepository(e.target.value)}
                    placeholder="owner/repo"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
                <div className="w-full md:w-2/3">
                  <label className="block text-xs font-medium text-slate-400 mb-1">Semantic & Hybrid Search Query</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="e.g. JWT token validation handler or function calculateScore"
                      className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500"
                      required
                    />
                    <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center space-x-3">
                  <Filter className="w-4 h-4 text-slate-400" />
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none"
                  >
                    <option value="">All Languages</option>
                    <option value="python">Python</option>
                    <option value="typescript">TypeScript</option>
                    <option value="javascript">JavaScript</option>
                    <option value="java">Java</option>
                    <option value="go">Go</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center space-x-2 px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm rounded-lg transition-colors disabled:opacity-50"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{loading ? 'Searching...' : 'Search Codebase'}</span>
                </button>
              </div>
            </form>
          </Card>

          {/* Search Results Display */}
          {loading ? (
            <LoadingSkeleton count={3} />
          ) : searched && results.length === 0 ? (
            <EmptyState
              title="No Code Results Found"
              description={`No matching code chunks found in '${repository}' for query '${query}'. Ensure the repository has been indexed.`}
            />
          ) : (
            <div className="space-y-4">
              {results.map((r) => (
                <div
                  key={r.chunk_id}
                  className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2 font-mono text-blue-400">
                      <Code2 className="w-4 h-4 text-blue-500" />
                      <span>{r.citation}</span>
                      {r.symbol && (
                        <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded font-sans">
                          {r.symbol_type}: {r.symbol}
                        </span>
                      )}
                    </div>
                    <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded font-mono">
                      RRF Score: {r.score}
                    </span>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre">
                    {r.content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
