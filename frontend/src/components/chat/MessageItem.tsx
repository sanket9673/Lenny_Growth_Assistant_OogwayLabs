import React from 'react';
import { Message } from '../../context/ChatContext';
import { CitationPopover } from './CitationPopover';
import { Bot, User, Sparkles, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';

export const MessageItem: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex space-x-4 p-4 rounded-2xl transition-colors ${
        isUser
          ? 'bg-slate-100/80 dark:bg-slate-800/40 ml-12'
          : 'bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800/60 mr-12'
      }`}
    >
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
          isUser
            ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900'
            : 'bg-gradient-to-tr from-orange-500 to-amber-500 text-white shadow-sm shadow-orange-500/20'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      <div className="flex-1 overflow-hidden space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">
            {isUser ? 'You' : 'Lenny Growth Assistant'}
          </span>
          <span className="text-[10px] text-slate-400 font-mono">{message.timestamp}</span>
        </div>

        {/* Skill Execution Multi-Pass Banner */}
        {message.skillProgress && (
          <div className="my-2 p-3 bg-gradient-to-r from-orange-500/10 via-amber-500/10 to-transparent border-l-2 border-orange-500 rounded-r-lg">
            <div className="flex items-center justify-between text-xs font-medium text-orange-600 dark:text-orange-400 mb-1">
              <span className="flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 animate-spin" />
                <span>Skill Execution: {message.skillProgress.skillName}</span>
              </span>
              <span className="text-[10px] font-mono">
                Phase {message.skillProgress.phaseIndex} of {message.skillProgress.totalPhases}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              {message.skillProgress.currentPhase}
            </p>
            <div className="w-full bg-slate-200 dark:bg-slate-800 h-1 rounded-full mt-2 overflow-hidden">
              <div
                className="bg-orange-500 h-full transition-all duration-300"
                style={{
                  width: `${(message.skillProgress.phaseIndex / message.skillProgress.totalPhases) * 100}%`,
                }}
              />
            </div>
          </div>
        )}

        {/* Message Content Body */}
        <div className="prose dark:prose-invert prose-slate text-xs sm:text-sm leading-relaxed max-w-none whitespace-pre-wrap">
          {message.content}
          {message.isStreaming && (
            <span className="inline-block w-1.5 h-4 ml-1 bg-orange-500 animate-pulse align-middle" />
          )}
        </div>

        {/* Citation Badges */}
        {message.citations && message.citations.length > 0 && (
          <div className="pt-2 flex flex-wrap gap-1.5 items-center">
            <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider mr-1">
              Sources:
            </span>
            {message.citations.map((cit) => (
              <CitationPopover key={cit.id} citation={cit}>
                <button className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[11px] font-mono bg-orange-500/10 text-orange-600 dark:text-orange-400 hover:bg-orange-500/20 border border-orange-500/20 transition-colors">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>
                    [{cit.speaker} - Ep {cit.episodeNum || 'Ref'}]
                  </span>
                </button>
              </CitationPopover>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};
