'use client';

import { useEffect, useState } from 'react';
import { getHealth } from '@/lib/api';

export function StatusIndicator() {
  const [status, setStatus] = useState<'checking' | 'connected' | 'unavailable'>('checking');

  useEffect(() => {
    let isMounted = true;
    getHealth()
      .then((res) => {
        if (isMounted && res.status === 'ok') {
          setStatus('connected');
        }
      })
      .catch(() => {
        if (isMounted) {
          setStatus('unavailable');
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (status === 'checking') {
    return (
      <div className="flex items-center space-x-2 text-xs text-zinc-400">
        <span className="h-2 w-2 rounded-full bg-zinc-500 animate-pulse" />
        <span>Connecting...</span>
      </div>
    );
  }

  if (status === 'connected') {
    return (
      <div className="flex items-center space-x-2 text-xs text-emerald-400 font-medium">
        <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
        <span>Backend Connected</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-xs text-rose-400 font-medium">
      <span className="h-2 w-2 rounded-full bg-rose-500" />
      <span>Backend Unavailable</span>
    </div>
  );
}
