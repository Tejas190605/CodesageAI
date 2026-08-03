'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { StatusIndicator } from './StatusIndicator';
import { Bot, LayoutDashboard, GitBranch, Settings } from 'lucide-react';

export function Topbar() {
  const pathname = usePathname();

  return (
    <header className="h-16 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Mobile Brand / Title */}
      <div className="flex items-center space-x-3 md:hidden">
        <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
          <Bot className="h-5 w-5" />
        </div>
        <span className="font-bold text-sm text-zinc-100">CodeSage AI</span>
      </div>

      {/* Mobile Navigation Links */}
      <nav className="flex md:hidden space-x-4 text-xs font-medium">
        <Link
          href="/"
          className={`flex items-center space-x-1 ${
            pathname === '/' ? 'text-indigo-400 font-semibold' : 'text-zinc-400'
          }`}
        >
          <LayoutDashboard className="h-3.5 w-3.5" />
          <span>Dashboard</span>
        </Link>
        <Link
          href="/repos"
          className={`flex items-center space-x-1 ${
            pathname.startsWith('/repos') ? 'text-indigo-400 font-semibold' : 'text-zinc-400'
          }`}
        >
          <GitBranch className="h-3.5 w-3.5" />
          <span>Repos</span>
        </Link>
        <Link
          href="/settings"
          className={`flex items-center space-x-1 ${
            pathname.startsWith('/settings') ? 'text-indigo-400 font-semibold' : 'text-zinc-400'
          }`}
        >
          <Settings className="h-3.5 w-3.5" />
          <span>Settings</span>
        </Link>
      </nav>

      {/* Desktop Search / Info Placeholder */}
      <div className="hidden md:flex items-center space-x-4">
        <span className="text-xs text-zinc-500 font-mono">v0.3.0 • FastAPI + Next.js</span>
      </div>

      {/* Right Side Status Dot */}
      <div className="flex items-center space-x-4">
        <StatusIndicator />
      </div>
    </header>
  );
}
