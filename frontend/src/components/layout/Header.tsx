import React from 'react';
import { useModel, ProviderType } from '../../context/ModelContext';
import { useChat } from '../../context/ChatContext';
import { Sparkles, Bot, Zap, Cpu, Github, Layout, Moon, Sun } from 'lucide-react';

interface HeaderProps {
  darkMode: boolean;
  setDarkMode: React.Dispatch<React.SetStateAction<boolean>>;
}

export const Header: React.FC<HeaderProps> = ({ darkMode, setDarkMode }) => {
  const { selectedProvider, selectProvider, healthStatus } = useModel();
  const { isArtifactPanelOpen, setIsArtifactPanelOpen } = useChat();

  const getStatusBadge = (provider: ProviderType) => {
    const isHealthy = healthStatus[provider];
    return (
      <span
        className={`inline-block w-2 h-2 rounded-full mr-2 ${
          isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
        }`}
      />
    );
  };

  return (
    <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-4 flex items-center justify-between sticky top-0 z-30 transition-colors">
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-orange-500 to-amber-400 flex items-center justify-center text-white font-bold shadow-sm shadow-orange-500/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="font-semibold text-slate-900 dark:text-slate-100 tracking-tight text-sm">
            Lenny Growth Assistant
          </span>
          <span className="px-2 py-0.5 text-[10px] font-mono font-medium rounded-full bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
            YC S24
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Provider Selector Switcher */}
        <div className="flex items-center bg-slate-100 dark:bg-slate-800/80 p-1 rounded-lg border border-slate-200 dark:border-slate-700/60">
          <button
            onClick={() => selectProvider('anthropic')}
            className={`flex items-center px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
              selectedProvider === 'anthropic'
                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {getStatusBadge('anthropic')}
            <Bot className="w-3.5 h-3.5 mr-1.5" />
            Claude 3.5
          </button>

          <button
            onClick={() => selectProvider('groq')}
            className={`flex items-center px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
              selectedProvider === 'groq'
                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {getStatusBadge('groq')}
            <Zap className="w-3.5 h-3.5 mr-1.5" />
            Groq Llama 3.3
          </button>

          <button
            onClick={() => selectProvider('ollama')}
            className={`flex items-center px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
              selectedProvider === 'ollama'
                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {getStatusBadge('ollama')}
            <Cpu className="w-3.5 h-3.5 mr-1.5" />
            Local Ollama
          </button>
        </div>

        {/* Artifact Toggle */}
        <button
          onClick={() => setIsArtifactPanelOpen(!isArtifactPanelOpen)}
          className={`p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors ${
            isArtifactPanelOpen ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100' : ''
          }`}
          title="Toggle Artifact Panel (Cmd+.)"
        >
          <Layout className="w-4 h-4" />
        </button>

        {/* Dark/Light Toggle */}
        <button
          onClick={() => setDarkMode((prev) => !prev)}
          className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title="Toggle theme"
        >
          {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          <Github className="w-4 h-4" />
        </a>
      </div>
    </header>
  );
};
