import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface ArtifactData {
  id?: string;
  artifact_key: string;
  title: string;
  type: 'html' | 'markdown' | 'svg';
  content: string;
  version: number;
  session_id: string;
}

interface ArtifactContextType {
  activeArtifact: ArtifactData | null;
  artifactHistory: ArtifactData[];
  isOpen: boolean;
  setIsOpen: (val: boolean) => void;
  openArtifact: (artifact: ArtifactData) => void;
  closeArtifact: () => void;
  selectVersion: (version: number) => void;
  processStreamEvent: (event: string, payload: any) => void;
}

const ArtifactContext = createContext<ArtifactContextType | undefined>(undefined);

export const ArtifactProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [activeArtifact, setActiveArtifact] = useState<ArtifactData | null>(null);
  const [artifactHistory, setArtifactHistory] = useState<ArtifactData[]>([]);
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const openArtifact = useCallback((artifact: ArtifactData) => {
    setActiveArtifact(artifact);
    setIsOpen(true);
  }, []);

  const closeArtifact = useCallback(() => {
    setIsOpen(false);
  }, []);

  const selectVersion = useCallback((version: number) => {
    const found = artifactHistory.find((item) => item.version === version);
    if (found) {
      setActiveArtifact(found);
    }
  }, [artifactHistory]);

  const processStreamEvent = useCallback((event: string, payload: any) => {
    if (event === 'artifact_start') {
      const newArtifact: ArtifactData = {
        artifact_key: payload.artifact_key,
        title: payload.title,
        type: payload.type,
        content: '',
        version: payload.version || 1,
        session_id: payload.session_id,
      };
      setActiveArtifact(newArtifact);
      setIsOpen(true);
      setArtifactHistory((prev) => [...prev.filter(a => a.version !== newArtifact.version), newArtifact]);
    } else if (event === 'artifact_chunk') {
      setActiveArtifact((prev) => {
        if (!prev || prev.artifact_key !== payload.artifact_key) return prev;
        const updated = { ...prev, content: prev.content + payload.chunk };
        return updated;
      });
    } else if (event === 'artifact_complete') {
      setActiveArtifact((prev) => {
        if (!prev || prev.artifact_key !== payload.artifact_key) return prev;
        const completed = { ...prev, content: payload.content, id: payload.id };
        
        setArtifactHistory((history) => {
          const idx = history.findIndex(a => a.artifact_key === completed.artifact_key && a.version === completed.version);
          if (idx >= 0) {
            const copy = [...history];
            copy[idx] = completed;
            return copy;
          }
          return [...history, completed];
        });
        
        return completed;
      });
    }
  }, []);

  return (
    <ArtifactContext.Provider
      value={{
        activeArtifact,
        artifactHistory,
        isOpen,
        setIsOpen,
        openArtifact,
        closeArtifact,
        selectVersion,
        processStreamEvent,
      }}
    >
      {children}
    </ArtifactContext.Provider>
  );
};

export const useArtifacts = (): ArtifactContextType => {
  const context = useContext(ArtifactContext);
  if (!context) {
    throw new Error('useArtifacts must be used within an ArtifactProvider');
  }
  return context;
};
