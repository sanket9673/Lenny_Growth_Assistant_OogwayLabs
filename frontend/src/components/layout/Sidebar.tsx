import React from 'react';
import { useSession, Session } from '../../context/SessionContext';
import { Plus, Trash2, MessageSquare, ChevronLeft, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (val: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, setIsCollapsed }) => {
  const { sessions, activeSessionId, createSession, selectSession, deleteSession } = useSession();

  const groupSessions = (list: Session[]) => {
    const today: Session[] = [];
    const last7Days: Session[] = [];
    const older: Session[] = [];

    const now = new Date();
    list.forEach((session) => {
      const created = new Date(session.createdAt || Date.now());
      const diffTime = Math.abs(now.getTime() - created.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays <= 1) today.push(session);
      else if (diffDays <= 7) last7Days.push(session);
      else older.push(session);
    });

    return { today, last7Days, older };
  };

  const grouped = groupSessions(sessions);

  const renderGroup = (title: string, items: Session[]) => {
    if (items.length === 0) return null;
    return (
      <div className="mb-4">
        <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-3 mb-1.5">
          {title}
        </h4>
        <div className="space-y-0.5">
          {items.map((s) => {
            const isActive = s.id === activeSessionId;
            return (
              <div
                key={s.id}
                onClick={() => selectSession(s.id)}
                className={`group relative flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium cursor-pointer transition-all ${
                  isActive
                    ? 'bg-slate-200/70 dark:bg-slate-800 text-slate-900 dark:text-slate-100 font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/50 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                <div className="flex items-center space-x-2 truncate pr-4">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{s.title || 'Untitled Session'}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(s.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-rose-500/10 hover:text-rose-500 transition-all"
                  title="Delete session"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <motion.aside
      animate={{ width: isCollapsed ? 64 : 260 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="relative flex flex-col h-[calc(100vh-3.5rem)] border-r border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 backdrop-blur-sm shrink-0 z-20"
    >
      <div className="p-3 flex items-center justify-between border-b border-slate-200/60 dark:border-slate-800/60">
        {!isCollapsed && (
          <button
            onClick={() => createSession()}
            className="w-full flex items-center justify-center space-x-2 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 font-medium py-2 px-3 rounded-lg text-xs shadow-sm transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Chat</span>
            <span className="text-[10px] font-mono opacity-60 ml-auto">⌘K</span>
          </button>
        )}

        {isCollapsed && (
          <button
            onClick={() => createSession()}
            className="w-full flex items-center justify-center p-2 rounded-lg bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900"
            title="New Chat (⌘K)"
          >
            <Plus className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-2 scrollbar-thin">
        {!isCollapsed ? (
          <>
            {renderGroup('Today', grouped.today)}
            {renderGroup('Previous 7 Days', grouped.last7Days)}
            {renderGroup('Older', grouped.older)}
          </>
        ) : (
          <div className="flex flex-col items-center space-y-2 pt-2">
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => selectSession(s.id)}
                className={`p-2.5 rounded-lg text-xs transition-colors ${
                  s.id === activeSessionId
                    ? 'bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-slate-100'
                    : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
                title={s.title}
              >
                <MessageSquare className="w-4 h-4" />
              </button>
            ))}
          </div>
        )}
      </div>

      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-3 top-10 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full p-1 text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 shadow-sm z-30"
      >
        {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
      </button>
    </motion.aside>
  );
};
