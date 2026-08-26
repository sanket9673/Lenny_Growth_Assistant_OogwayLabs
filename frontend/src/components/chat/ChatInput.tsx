import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../../context/ChatContext';
import { Send, Square, Zap, FileText, Search } from 'lucide-react';

export const ChatInput: React.FC = () => {
  const [input, setInput] = useState('');
  const { sendMessage, isStreaming, stopStreaming } = useChat();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handlePreset = (presetText: string, skill: string) => {
    sendMessage(presetText, skill);
  };

  return (
    <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
      {/* Quick Skill Presets Bar */}
      <div className="flex items-center space-x-2 mb-3 overflow-x-auto pb-1 scrollbar-none">
        <button
          onClick={() =>
            handlePreset('Generate a Ship 30 essay on product-market fit metrics.', 'ship30')
          }
          className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-orange-500/10 hover:text-orange-500 transition-colors whitespace-nowrap border border-slate-200 dark:border-slate-700"
        >
          <Zap className="w-3.5 h-3.5 text-orange-500" />
          <span>⚡ Ship 30 Essay (~1,250 words)</span>
        </button>

        <button
          onClick={() =>
            handlePreset('Draft a B2B product strategy roadmap framework.', 'product_strategy')
          }
          className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-orange-500/10 hover:text-orange-500 transition-colors whitespace-nowrap border border-slate-200 dark:border-slate-700"
        >
          <FileText className="w-3.5 h-3.5 text-blue-500" />
          <span>📊 Product Strategy Artifact</span>
        </button>

        <button
          onClick={() =>
            handlePreset('What are Marty Cagan’s core principles on product teams?', 'rag_qa')
          }
          className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-orange-500/10 hover:text-orange-500 transition-colors whitespace-nowrap border border-slate-200 dark:border-slate-700"
        >
          <Search className="w-3.5 h-3.5 text-emerald-500" />
          <span>🔍 Grounded Transcript Q&A</span>
        </button>
      </div>

      {/* Input Box Form */}
      <form onSubmit={handleSubmit} className="relative flex items-end bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 focus-within:border-orange-500 dark:focus-within:border-orange-500 transition-all p-2">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about growth, product strategy, or search podcast transcripts..."
          rows={1}
          className="flex-1 bg-transparent border-none resize-none focus:outline-none focus:ring-0 text-xs sm:text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 px-2 py-1 max-h-40 scrollbar-thin"
        />

        <div className="flex items-center space-x-1 ml-2">
          {isStreaming ? (
            <button
              type="button"
              onClick={stopStreaming}
              className="p-2 rounded-lg bg-rose-500 hover:bg-rose-600 text-white transition-colors"
              title="Stop generating"
            >
              <Square className="w-4 h-4 fill-current" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="p-2 rounded-lg bg-orange-500 hover:bg-orange-600 disabled:opacity-40 disabled:hover:bg-orange-500 text-white transition-colors shadow-sm shadow-orange-500/20"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </div>
      </form>
    </div>
  );
};
