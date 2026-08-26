import React, { createContext, useContext, useState, useRef } from 'react';
import { useModel } from './ModelContext';
import { useSession } from './SessionContext';
import { useArtifacts } from './ArtifactContext';

export interface Citation {
  id: string;
  speaker: string;
  episodeTitle: string;
  episodeNum?: number | string;
  timestamp: string;
  snippet: string;
}

export interface SkillProgress {
  skillName: string;
  currentPhase: string;
  totalPhases: number;
  phaseIndex: number;
  details?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  citations?: Citation[];
  skillProgress?: SkillProgress;
  isStreaming?: boolean;
}

interface ChatContextType {
  messages: Message[];
  isStreaming: boolean;
  activeTokenBuffer: string;
  activeArtifact: any | null;
  isArtifactPanelOpen: boolean;
  setIsArtifactPanelOpen: (open: boolean) => void;
  sendMessage: (content: string, presetSkill?: string) => Promise<void>;
  stopStreaming: () => void;
  clearChat: () => void;
  setActiveArtifact: (artifact: any | null) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [activeTokenBuffer, setActiveTokenBuffer] = useState<string>('');

  const { selectedProvider, selectedModel, setIsOllamaOfflineModalOpen } = useModel();
  const { activeSessionId } = useSession();
  const { 
    activeArtifact, 
    openArtifact, 
    isOpen: isArtifactPanelOpen, 
    setIsOpen: setIsArtifactPanelOpen, 
    processStreamEvent 
  } = useArtifacts();

  const abortControllerRef = useRef<AbortController | null>(null);

  const stopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  };

  const clearChat = () => {
    stopStreaming();
    setMessages([]);
  };

  const setActiveArtifact = (artifact: any | null) => {
    if (artifact) {
      openArtifact({
        artifact_key: artifact.artifact_key || artifact.key,
        title: artifact.title,
        type: artifact.type,
        content: artifact.content,
        version: artifact.version || 1,
        session_id: activeSessionId || '',
      });
    }
  };

  const sendMessage = async (content: string, presetSkill?: string) => {
    if (!content.trim() && !presetSkill) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const assistantMsgId = `asst-${Date.now()}`;
    const initialAssistantMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setIsStreaming(true);
    setActiveTokenBuffer('');

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortControllerRef.current.signal,
        body: JSON.stringify({
          message: content,
          session_id: activeSessionId,
          provider: selectedProvider,
          model: selectedModel,
          skill_preset: presetSkill,
        }),
      });

      if (!response.ok) {
        if (response.status === 503 && selectedProvider === 'ollama') {
          setIsOllamaOfflineModalOpen(true);
        }
        throw new Error(`HTTP Error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No response reader available');

      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.replace('data: ', '').trim();
          if (jsonStr === '[DONE]') break;

          try {
            const data = JSON.parse(jsonStr);

            if (data.type === 'token') {
              accumulatedContent += data.text;
              setActiveTokenBuffer(accumulatedContent);
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, content: accumulatedContent } : msg
                )
              );
            } else if (data.type === 'skill_progress') {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? {
                        ...msg,
                        skillProgress: {
                          skillName: data.skillName,
                          currentPhase: data.currentPhase,
                          totalPhases: data.totalPhases,
                          phaseIndex: data.phaseIndex,
                          details: data.details,
                        },
                      }
                    : msg
                )
              );
            } else if (data.type === 'citations') {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, citations: data.citations } : msg
                )
              );
            } else if (data.type === 'artifact') {
              openArtifact({
                artifact_key: data.artifact.artifact_key,
                title: data.artifact.title,
                type: data.artifact.type,
                content: data.artifact.content,
                version: data.artifact.version || 1,
                session_id: activeSessionId || '',
              });
            } else if (
              data.type === 'artifact_start' ||
              data.type === 'artifact_chunk' ||
              data.type === 'artifact_complete'
            ) {
              processStreamEvent(data.type, data.data);
            }
          } catch {
            // Raw text chunk fallback
            accumulatedContent += jsonStr;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId ? { ...msg, content: accumulatedContent } : msg
              )
            );
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Stream aborted by user');
      } else {
        console.error('Streaming error:', err);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content:
                    msg.content +
                    '\n\n*[Error: Unable to complete response stream. Please verify LLM backend connection.]*',
                }
              : msg
          )
        );
      }
    } finally {
      setIsStreaming(false);
      setMessages((prev) =>
        prev.map((msg) => (msg.id === assistantMsgId ? { ...msg, isStreaming: false } : msg))
      );
      abortControllerRef.current = null;
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        isStreaming,
        activeTokenBuffer,
        activeArtifact,
        isArtifactPanelOpen,
        setIsArtifactPanelOpen,
        sendMessage,
        stopStreaming,
        clearChat,
        setActiveArtifact,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used within ChatProvider');
  return ctx;
};
