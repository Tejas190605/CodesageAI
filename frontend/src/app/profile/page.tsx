'use client';

import { useState, useEffect } from 'react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/Card';
import { LoadingSkeleton, ErrorState } from '@/components/ui/States';
import { getCurrentUser, logoutUser } from '@/lib/api';
import { User } from '@/lib/types';
import { User as UserIcon, Shield, Building2, Mail, LogOut, CheckCircle } from 'lucide-react';

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCurrentUser()
      .then((data) => {
        setUser(data);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch user profile.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleLogout = async () => {
    try {
      await logoutUser();
      window.location.href = '/login';
    } catch {
      alert('Failed to sign out.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <PageHeader
        title="User Profile & Account Settings"
        description="Manage your authenticated GitHub session, organization memberships, and security roles"
        action={
          <button
            onClick={handleLogout}
            className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-rose-600/20 text-rose-300 border border-rose-500/30 hover:bg-rose-600/30 transition shadow-sm"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign Out</span>
          </button>
        }
      />

      {loading ? (
        <LoadingSkeleton count={3} />
      ) : error ? (
        <ErrorState message={error} />
      ) : user ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* User Info Overview Card */}
          <Card className="md:col-span-1 p-6 text-center flex flex-col items-center space-y-4 bg-zinc-900/60 border-zinc-800">
            <div className="relative">
              {user.avatar_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={user.avatar_url}
                  alt={user.username}
                  className="w-20 h-20 rounded-full border-2 border-indigo-500/30 shadow-md"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-zinc-800 border-2 border-indigo-500/30 flex items-center justify-center text-zinc-400">
                  <UserIcon className="h-10 w-10" />
                </div>
              )}
              <span className="absolute bottom-0 right-0 p-1 bg-emerald-500 rounded-full border-2 border-zinc-950" />
            </div>

            <div>
              <h2 className="text-lg font-bold text-zinc-100">{user.name || user.username}</h2>
              <p className="text-xs text-zinc-400 font-mono">@{user.username}</p>
            </div>

            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase tracking-wide">
              <Shield className="w-3.5 h-3.5" /> {user.role}
            </div>
          </Card>

          {/* Account Details & Organizations */}
          <div className="md:col-span-2 space-y-6">
            <Card className="p-6 space-y-4 bg-zinc-900/40 border-zinc-800/80">
              <h3 className="text-sm font-semibold text-zinc-200 border-b border-zinc-800 pb-2">
                Account Details
              </h3>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-zinc-500 block mb-1">GitHub ID</span>
                  <span className="font-mono text-zinc-200">{user.github_id}</span>
                </div>
                <div>
                  <span className="text-zinc-500 block mb-1">Email</span>
                  <span className="text-zinc-200 flex items-center space-x-1">
                    <Mail className="h-3.5 w-3.5 text-zinc-400" />
                    <span>{user.email || 'No public email'}</span>
                  </span>
                </div>
              </div>
            </Card>

            <Card className="p-6 space-y-4 bg-zinc-900/40 border-zinc-800/80">
              <h3 className="text-sm font-semibold text-zinc-200 border-b border-zinc-800 pb-2 flex items-center justify-between">
                <span>Connected Organizations</span>
                <span className="text-xs font-normal text-zinc-400">({user.organizations?.length ?? 0})</span>
              </h3>

              {(!user.organizations || user.organizations.length === 0) ? (
                <p className="text-xs text-zinc-500 italic">No connected GitHub organizations detected.</p>
              ) : (
                <div className="divide-y divide-zinc-800/60">
                  {user.organizations.map((org) => (
                    <div key={org.id} className="py-2.5 flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-3">
                        <Building2 className="h-4 w-4 text-indigo-400" />
                        <span className="font-medium text-zinc-200">@{org.login}</span>
                      </div>
                      <span className="text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 flex items-center space-x-1">
                        <CheckCircle className="h-3 w-3" />
                        <span>Active</span>
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  );
}
