'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, GitBranch, Settings, Bot, ShieldCheck, Activity, AppWindow, User, LogIn, Cpu, Search, Sliders, BarChart3, FileText } from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Repositories', href: '/repos', icon: GitBranch },
  { name: 'Code Search', href: '/search', icon: Search },
  { name: 'Policies', href: '/policies', icon: Sliders },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Audit Log', href: '/audit-log', icon: FileText },
  { name: 'Job Queue', href: '/jobs', icon: Activity },
  { name: 'AI Platform', href: '/ai-settings', icon: Cpu },
  { name: 'Installations', href: '/installations', icon: AppWindow },
  { name: 'Profile', href: '/profile', icon: User },
  { name: 'Sign In', href: '/login', icon: LogIn },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-zinc-800 bg-zinc-950 flex flex-col justify-between hidden md:flex shrink-0">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-zinc-800 space-x-3">
          <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/20">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h1 className="font-bold text-sm text-zinc-100 tracking-wide">CodeSage AI</h1>
            <p className="text-[11px] text-zinc-400">Developer Assistant</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === '/'
                ? pathname === '/'
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-zinc-900 text-indigo-400 border border-zinc-800'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-indigo-400' : 'text-zinc-500'}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-zinc-800/60 text-xs text-zinc-500 space-y-2">
        <div className="flex items-center space-x-2 text-zinc-400">
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
          <span>GitHub OAuth & App OAuth</span>
        </div>
        <p className="text-[10px]">Gemini 2.5 Flash Engine</p>
      </div>
    </aside>
  );
}

export default Sidebar;
