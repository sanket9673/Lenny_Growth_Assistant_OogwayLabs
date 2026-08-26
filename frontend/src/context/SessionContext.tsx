import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export interface Session {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

interface SessionContextType {
  sessions: Session[];
  activeSessionId: string | null;
  isLoading: boolean;
  createSession: (title?: string) => Promise<string>;
  selectSession: (id: string) => void;
  deleteSession: (id: string) => Promise<void>;
  updateSessionTitle: (id: string, title: string) => Promise<void>;
  refreshSessions: () => Promise<void>;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshSessions = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
        if (data.length > 0 && !activeSessionId) {
          setActiveSessionId(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    } finally {
      setIsLoading(false);
    }
  }, [activeSessionId]);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  const createSession = async (title: string = 'New Session'): Promise<string> => {
    try {
      const response = await fetch('/api/v1/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
      if (!response.ok) throw new Error('Failed to create session');
      const newSession: Session = await response.json();
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      return newSession.id;
    } catch (err) {
      console.error('Error creating session:', err);
      const fallbackId = `session-${Date.now()}`;
      const fallbackSession: Session = {
        id: fallbackId,
        title,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      setSessions((prev) => [fallbackSession, ...prev]);
      setActiveSessionId(fallbackId);
      return fallbackId;
    }
  };

  const selectSession = (id: string) => {
    setActiveSessionId(id);
  };

  const deleteSession = async (id: string) => {
    try {
      await fetch(`/api/v1/sessions/${id}`, { method: 'DELETE' });
    } catch (err) {
      console.error('Failed to delete session on backend:', err);
    } finally {
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) {
        const remaining = sessions.filter((s) => s.id !== id);
        setActiveSessionId(remaining.length > 0 ? remaining[0].id : null);
      }
    }
  };

  const updateSessionTitle = async (id: string, title: string) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, title, updatedAt: new Date().toISOString() } : s))
    );
    try {
      await fetch(`/api/v1/sessions/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
    } catch (err) {
      console.error('Failed to update session title:', err);
    }
  };

  return (
    <SessionContext.Provider
      value={{
        sessions,
        activeSessionId,
        isLoading,
        createSession,
        selectSession,
        deleteSession,
        updateSessionTitle,
        refreshSessions,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession must be used within SessionProvider');
  return ctx;
};
