import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = '', ...props }: CardProps) {
  return (
    <div
      className={`bg-zinc-900/70 border border-zinc-800/80 rounded-xl p-5 shadow-sm hover:border-zinc-700/80 transition-colors ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
