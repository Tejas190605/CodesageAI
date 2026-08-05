'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { LoadingSkeleton } from '@/components/ui/States';
import { getAuditEvents } from '@/lib/api';
import { AuditEventInfo } from '@/lib/types';
import { ShieldCheck, Filter, Clock, User, Terminal } from 'lucide-react';

export default function AuditLogPage() {
  const [events, setEvents] = useState<AuditEventInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [eventType, setEventType] = useState<string>('');

  useEffect(() => {
    async function loadEvents() {
      try {
        setLoading(true);
        const res = await getAuditEvents(eventType || undefined, 50, 0);
        setEvents(res.events || []);
      } catch (err) {
        console.error('Failed to load audit events:', err);
      } finally {
        setLoading(false);
      }
    }
    loadEvents();
  }, [eventType]);

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col pl-64">
        <PageHeader
          title="System Audit & Security Activity Log"
          description="Immutable timeline of authentication events, repository indexing, policy updates, and code reviews."
        />
        <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
          {/* Audit Event Filter Header */}
          <Card className="p-5 bg-slate-900/60 border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Security Audit Trail</h3>
                <p className="text-xs text-slate-400">All sensitive metadata, API tokens, and credentials are automatically scrubbed.</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Filter className="w-4 h-4 text-slate-400" />
              <select
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
                className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none"
              >
                <option value="">All Event Types</option>
                <option value="user.login">User Login</option>
                <option value="user.logout">User Logout</option>
                <option value="repository.indexed">Repository Indexed</option>
                <option value="policy.updated">Policy Updated</option>
                <option value="review.completed">Review Completed</option>
              </select>
            </div>
          </Card>

          {/* Audit Events List */}
          {loading ? (
            <LoadingSkeleton count={4} />
          ) : events.length === 0 ? (
            <Card className="p-8 text-center bg-slate-900/60 border-slate-800 space-y-2">
              <Terminal className="w-8 h-8 text-slate-500 mx-auto" />
              <h3 className="text-base font-medium text-slate-200">No Audit Events Recorded</h3>
              <p className="text-xs text-slate-400">Application audit events will populate as authentication and repository reviews take place.</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {events.map((ev) => (
                <div
                  key={ev.id}
                  className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-3">
                      <span className="px-2.5 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded font-mono font-semibold">
                        {ev.event_type}
                      </span>
                      <span className="flex items-center space-x-1 text-slate-400">
                        <User className="w-3.5 h-3.5 text-slate-500" />
                        <span>Actor: <strong className="text-slate-200">{ev.actor}</strong></span>
                      </span>
                    </div>

                    <div className="flex items-center space-x-1 text-slate-500 font-mono">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{ev.created_at ? new Date(ev.created_at).toLocaleString() : ''}</span>
                    </div>
                  </div>

                  {ev.description && (
                    <p className="text-xs text-slate-300 pl-1">{ev.description}</p>
                  )}

                  {ev.metadata && Object.keys(ev.metadata).length > 0 && (
                    <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-400">
                      {JSON.stringify(ev.metadata)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
