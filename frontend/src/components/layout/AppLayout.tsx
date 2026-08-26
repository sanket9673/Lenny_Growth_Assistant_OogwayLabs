import React, { useState, useEffect } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ChatFeed } from '../chat/ChatFeed';
import { ChatInput } from '../chat/ChatInput';
import { useChat } from '../../context/ChatContext';
import { useSession } from '../../context/SessionContext';
import { OllamaSetupModal } from '../ui/OllamaSetupModal';
import { ArtifactViewer } from '../artifacts/ArtifactViewer';
import { ExternalLink } from 'lucide-react';

export const AppLayout: React.FC = () => {
  const [darkMode, setDarkMode] = useState<boolean>(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);
  const { activeArtifact, isArtifactPanelOpen, setIsArtifactPanelOpen } = useChat();
  const { createSession } = useSession();

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Global Keyboard Navigation Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        createSession();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === '.') {
        e.preventDefault();
        setIsArtifactPanelOpen(!isArtifactPanelOpen);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [createSession, isArtifactPanelOpen, setIsArtifactPanelOpen]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans selection:bg-orange-500/20 selection:text-orange-500 transition-colors">
      <Header darkMode={darkMode} setDarkMode={setDarkMode} />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Navigation Sidebar */}
        <Sidebar isCollapsed={isSidebarCollapsed} setIsCollapsed={setIsSidebarCollapsed} />

        {/* Main Center Chat Workspace */}
        <main className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] relative overflow-hidden bg-white dark:bg-slate-900">
          <ChatFeed />
          <ChatInput />
        </main>

        {/* Right Sandboxed Artifact Viewer */}
        {isArtifactPanelOpen && (
          <aside className="w-[500px] border-l border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex flex-col h-[calc(100vh-3.5rem)] shadow-2xl z-20">
            {activeArtifact ? (
              <ArtifactViewer />
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 p-6 bg-white dark:bg-slate-900">
                <ExternalLink className="w-8 h-8 mb-2 stroke-[1.5]" />
                <p className="text-xs font-semibold">No active artifact selected</p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Execute product strategy or Ship 30 presets to view generated code and framework models here.
                </p>
              </div>
            )}
          </aside>
        )}
      </div>

      <OllamaSetupModal />
    </div>
  );
};
