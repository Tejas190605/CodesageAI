import React from 'react';

interface MarkdownViewerProps {
  content: string;
}

export function MarkdownViewer({ content }: MarkdownViewerProps) {
  if (!content) {
    return <p className="text-sm text-zinc-500 italic">No content provided.</p>;
  }

  // Parse markdown into lines for structured clean rendering
  const lines = content.split('\n');

  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBlockLines: string[] = [];
  let blockKey = 0;

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    // Code block toggle
    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        // End code block
        elements.push(
          <div key={`code-${blockKey++}`} className="my-3 rounded-lg border border-zinc-800 bg-zinc-950 p-4 font-mono text-xs text-zinc-200 overflow-x-auto">
            <pre className="whitespace-pre">{codeBlockLines.join('\n')}</pre>
          </div>
        );
        codeBlockLines = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      return;
    }

    // H1 Heading
    if (trimmed.startsWith('# ')) {
      elements.push(
        <h2 key={idx} className="text-xl font-bold text-zinc-100 mt-6 mb-3 border-b border-zinc-800 pb-2">
          {trimmed.replace('# ', '')}
        </h2>
      );
      return;
    }

    // H2 Heading
    if (trimmed.startsWith('## ')) {
      elements.push(
        <h3 key={idx} className="text-base font-semibold text-indigo-400 mt-5 mb-2 flex items-center space-x-2">
          <span>{trimmed.replace('## ', '')}</span>
        </h3>
      );
      return;
    }

    // H3 Heading
    if (trimmed.startsWith('### ')) {
      elements.push(
        <h4 key={idx} className="text-sm font-semibold text-zinc-200 mt-4 mb-1">
          {trimmed.replace('### ', '')}
        </h4>
      );
      return;
    }

    // Bold text / key-value lines
    if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
      elements.push(
        <p key={idx} className="text-sm font-semibold text-zinc-300 my-1">
          {trimmed.replace(/\*\*/g, '')}
        </p>
      );
      return;
    }

    // Empty lines
    if (!trimmed) {
      elements.push(<div key={idx} className="h-2" />);
      return;
    }

    // Regular paragraph
    elements.push(
      <p key={idx} className="text-sm text-zinc-300 leading-relaxed my-1">
        {line}
      </p>
    );
  });

  // Handle unclosed code block safely
  if (inCodeBlock && codeBlockLines.length > 0) {
    elements.push(
      <div key={`code-final`} className="my-3 rounded-lg border border-zinc-800 bg-zinc-950 p-4 font-mono text-xs text-zinc-200 overflow-x-auto">
        <pre className="whitespace-pre">{codeBlockLines.join('\n')}</pre>
      </div>
    );
  }

  return <div className="space-y-1">{elements}</div>;
}
