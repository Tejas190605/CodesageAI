'use client';

import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { StatusIndicator } from '@/components/layout/StatusIndicator';
import { Server, Key, Webhook } from 'lucide-react';

export default function SettingsPage() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

  return (
    <div className="space-y-8">
      <PageHeader
        title="Settings & Webhook Integration"
        description="Configuration overview, API connectivity, and GitHub Webhook integration guide."
      />

      {/* Backend Connection Status Card */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Server className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-zinc-100">FastAPI Backend Service</h2>
              <p className="text-xs text-zinc-400">REST API & Webhook Listener</p>
            </div>
          </div>
          <StatusIndicator />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
            <span className="text-zinc-500 block mb-1">API Base Endpoint</span>
            <span className="font-mono text-zinc-200 font-semibold">{apiBaseUrl}</span>
          </div>

          <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
            <span className="text-zinc-500 block mb-1">Health Probe Path</span>
            <span className="font-mono text-zinc-200 font-semibold">GET /health</span>
          </div>
        </div>
      </Card>

      {/* Environment & Configuration Setup Guide */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Backend Environment Variables Explanation */}
        <Card className="space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-zinc-800">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <Key className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-zinc-100">Backend Secrets & Config</h2>
              <p className="text-xs text-zinc-400">Configured in backend/.env</p>
            </div>
          </div>

          <div className="space-y-3 text-xs text-zinc-400">
            <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="font-mono font-semibold text-indigo-400">GEMINI_API_KEY</div>
              <p className="mt-1">API key for Google Gemini 2.5 Flash structured code analysis.</p>
            </div>

            <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="font-mono font-semibold text-indigo-400">GITHUB_TOKEN</div>
              <p className="mt-1">Personal Access Token with repo scope for PR diffs & discussion comments.</p>
            </div>

            <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="font-mono font-semibold text-indigo-400">GITHUB_WEBHOOK_SECRET</div>
              <p className="mt-1">HMAC-SHA256 secret key configured in GitHub repository Webhook settings.</p>
            </div>

            <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800">
              <div className="font-mono font-semibold text-indigo-400">CODESAGE_REPOSITORIES</div>
              <p className="mt-1">Comma-separated list of monitored repositories e.g. <code className="text-zinc-300">Tejas190605/ResumeIQ,owner/repo2</code>.</p>
            </div>
          </div>
        </Card>

        {/* GitHub Webhook Setup Step-by-Step */}
        <Card className="space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-zinc-800">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Webhook className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-zinc-100">GitHub Webhook Setup</h2>
              <p className="text-xs text-zinc-400">Step-by-step setup guide</p>
            </div>
          </div>

          <ol className="space-y-3 text-xs text-zinc-400 list-decimal list-inside">
            <li className="leading-relaxed">
              Start CodeSage FastAPI server on port 8000:
              <pre className="mt-1 p-2 rounded bg-zinc-950 text-indigo-300 font-mono text-[11px]">
                uvicorn app.main:app --reload --port 8000
              </pre>
            </li>
            <li className="leading-relaxed">
              Expose port 8000 using ngrok or an HTTPS tunnel:
              <pre className="mt-1 p-2 rounded bg-zinc-950 text-indigo-300 font-mono text-[11px]">
                ngrok http 8000
              </pre>
            </li>
            <li className="leading-relaxed">
              In GitHub Repository Settings → <strong>Webhooks</strong> → <strong>Add Webhook</strong>:
              <ul className="mt-1 pl-4 space-y-1 list-disc text-zinc-400">
                <li>Payload URL: <code className="text-zinc-200 font-mono">https://&lt;ngrok-url&gt;/webhook</code></li>
                <li>Content type: <code className="text-zinc-200 font-mono">application/json</code></li>
                <li>Secret: Matches <code className="text-zinc-200 font-mono">GITHUB_WEBHOOK_SECRET</code></li>
                <li>Events: Select <strong>Pull requests</strong> & <strong>Pushes</strong></li>
              </ul>
            </li>
          </ol>
        </Card>
      </div>
    </div>
  );
}
