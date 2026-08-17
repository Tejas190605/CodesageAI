'use client';

import { useState, useEffect } from 'react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { getAuthLoginUrl } from '@/lib/api';
import { ShieldCheck, Lock, CheckCircle2, UserCheck } from 'lucide-react';

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
  );
}

export default function LoginPage() {
  const [oauthEnabled, setOauthEnabled] = useState<boolean>(false);
  const [authUrl, setAuthUrl] = useState<string | null>(null);
  const [message, setMessage] = useState<string>('Loading GitHub OAuth status...');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    getAuthLoginUrl()
      .then((data) => {
        setOauthEnabled(data.oauth_enabled);
        if (data.auth_url) {
          setAuthUrl(data.auth_url);
        }
        if (data.message) {
          setMessage(data.message);
        }
      })
      .catch((err) => {
        setMessage(err instanceof Error ? err.message : 'Failed to reach auth service.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleGitHubSignIn = () => {
    if (authUrl) {
      window.location.href = authUrl;
    } else {
      alert(message || 'GitHub OAuth is currently unavailable. Please verify backend environment configuration.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <PageHeader
        title="Authentication & Single Sign-On"
        description="Secure multi-tenant authentication via GitHub OAuth 2.0 and HTTP-only session cookies"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Sign In Card */}
        <Card className="p-8 flex flex-col justify-between space-y-6 bg-gradient-to-b from-zinc-900 to-zinc-950 border-zinc-800">
          <div className="space-y-4">
            <div className="inline-flex p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <h2 className="text-xl font-bold text-zinc-100">Sign in to CodeSage AI</h2>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Authenticate with your GitHub developer or organization account to access repository reviews, AI findings, and background worker queues.
            </p>
          </div>

          <div className="space-y-4 pt-4 border-t border-zinc-800/80">
            <button
              onClick={handleGitHubSignIn}
              disabled={loading}
              className="w-full flex items-center justify-center space-x-3 px-5 py-3 rounded-xl bg-zinc-100 hover:bg-white text-zinc-950 font-semibold text-sm transition-all shadow-md active:scale-[0.99] disabled:opacity-50"
            >
              <GitHubIcon className="h-5 w-5 text-zinc-950" />
              <span>Sign in with GitHub</span>
            </button>

            {!oauthEnabled && !loading && (
              <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start space-x-2.5">
                <Lock className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{message}</span>
              </div>
            )}
          </div>
        </Card>

        {/* Enterprise Security Features Card */}
        <Card className="p-8 space-y-6 bg-zinc-900/40 border-zinc-800/80">
          <h3 className="text-base font-semibold text-zinc-200">Security & Authorization Standards</h3>
          <ul className="space-y-4 text-xs text-zinc-400">
            <li className="flex items-start space-x-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-zinc-200 font-medium block">HTTP-Only Encrypted Cookies</strong>
                <span>Session JWT tokens are stored in secure HTTP-only cookies, preventing XSS token theft.</span>
              </div>
            </li>
            <li className="flex items-start space-x-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-zinc-200 font-medium block">Role-Based Access Control (RBAC)</strong>
                <span>Granular permissions for Admins, Members, and Viewers across repository settings and job queues.</span>
              </div>
            </li>
            <li className="flex items-start space-x-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-zinc-200 font-medium block">GitHub App RS256 Tokens</strong>
                <span>Short-lived 10-minute JWT installation tokens with automatic background renewal.</span>
              </div>
            </li>
          </ul>

          <div className="pt-4 border-t border-zinc-800/80 flex items-center space-x-2 text-xs text-zinc-500">
            <UserCheck className="h-4 w-4 text-indigo-400" />
            <span>OAuth Scopes: <code className="text-zinc-400 bg-zinc-950 px-1.5 py-0.5 rounded">read:user</code>, <code className="text-zinc-400 bg-zinc-950 px-1.5 py-0.5 rounded">user:email</code>, <code className="text-zinc-400 bg-zinc-950 px-1.5 py-0.5 rounded">read:org</code></span>
          </div>
        </Card>
      </div>
    </div>
  );
}
