import React from 'react';
import * as Popover from '@radix-ui/react-popover';
import { Citation } from '../../context/ChatContext';
import { BookOpen, Copy, Check } from 'lucide-react';

interface CitationPopoverProps {
  citation: Citation;
  children: React.ReactNode;
}

export const CitationPopover: React.FC<CitationPopoverProps> = ({ citation, children }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    const textToCopy = `"${citation.snippet || ''}" - ${citation.speaker || 'Unknown'} (${citation.episodeTitle || 'Reference'})`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Popover.Root>
      <Popover.Trigger asChild>{children}</Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          className="w-80 bg-white dark:bg-slate-900 rounded-xl p-4 shadow-2xl border border-slate-200 dark:border-slate-800 z-50 animate-in fade-in-0 zoom-in-95"
          sideOffset={5}
        >
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center space-x-1.5 text-orange-500 font-medium text-xs">
              <BookOpen className="w-3.5 h-3.5" />
              <span>{citation.speaker}</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">{citation.timestamp}</span>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-300 italic mt-2.5 leading-relaxed bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
            "{citation.snippet}"
          </p>

          <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
            <span className="text-[10px] text-slate-400 truncate max-w-[180px]" title={citation.episodeTitle}>
              {citation.episodeTitle}
            </span>
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1 text-[10px] text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 font-medium px-2 py-1 rounded bg-slate-100 dark:bg-slate-800"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <Popover.Arrow className="fill-white dark:fill-slate-900" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
