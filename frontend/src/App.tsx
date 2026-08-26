import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Send, Plus, Search, MessageSquare, BookOpen, 
  ChevronRight, Sparkles, X, ExternalLink 
} from 'lucide-react';
import { ArtifactProvider, useArtifacts } from './context/ArtifactContext';
import { ArtifactViewer } from './components/artifacts/ArtifactViewer';

// API schemas & helpers
interface Citation {
  guest_name: string;
  transcript_title: string;
  speaker?: string;
  timestamp_start?: string;
  content: string;
}

interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  loading?: boolean;
}

interface ChatSession {
  id: string;
  provider: string;
  model: string;
}

const cleanArtifactTags = (text: string) => {
  return text.replace(/<lenny_artifact[\s\S]*?<\/lenny_artifact>/gi, '').trim();
};

const extractArtifacts = (text: string) => {
  const regex = /<lenny_artifact\s+key=["']([^"']+)["']\s+type=["'](html|markdown|svg)["']\s+title=["']([^"']+)["']>([\s\S]*?)<\/lenny_artifact>/gi;
  const matches = [];
  let match;
  while ((match = regex.exec(text)) !== null) {
    matches.push({
      key: match[1],
      type: match[2] as 'html' | 'markdown' | 'svg',
      title: match[3],
      content: match[4]
    });
  }
  return matches;
};

export function AppContent() {
  const { isOpen, openArtifact, processStreamEvent } = useArtifacts();
  
  // Layout & Resizing States
  const [sidebarWidth, setSidebarWidth] = useState(650);
  const [isResizing, setIsResizing] = useState(false);
  const [activeTab, setActiveTab] = useState<'search' | 'chat'>('chat');

  // Search Mode States
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchHasRun, setSearchHasRun] = useState(false);

  // Chat Mode States
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Draggable Split Pane Resize Handlers
  const startResizing = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback((e: MouseEvent) => {
    if (isResizing) {
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth > 350 && newWidth < window.innerWidth - 350) {
        setSidebarWidth(newWidth);
      }
    }
  }, [isResizing]);

  useEffect(() => {
    window.addEventListener('mousemove', resize);
    window.addEventListener('mouseup', stopResizing);
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    };
  }, [resize, stopResizing]);

  // Scroll chat to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load / Create active chat session on mount
  useEffect(() => {
    const initializeChat = async () => {
      try {
        const storedSessionId = localStorage.getItem('lenny_session_id');
        if (storedSessionId) {
          // Attempt to load existing session details
          const res = await fetch(`/api/v1/sessions/${storedSessionId}`);
          if (res.ok) {
            const data = await res.json();
            setActiveSession({ id: data.id, provider: data.provider, model: data.model });
            setMessages(data.messages || []);
            // Also retrieve existing artifacts for this session to load history context
            const artsRes = await fetch(`/api/v1/sessions/${storedSessionId}/artifacts`);
            if (artsRes.ok) {
              const arts = await artsRes.json();
              // Feed loaded artifacts into the artifact history state if needed
              for (const art of arts) {
                processStreamEvent('artifact_complete', art);
              }
            }
            return;
          }
        }
        
        // Stored session invalid or doesn't exist, create a new one
        await handleNewChat();
      } catch (err) {
        console.error('Failed to initialize session:', err);
      }
    };
    
    initializeChat();
  }, []);

  // Handle New Session Creation
  const handleNewChat = async () => {
    try {
      const res = await fetch('/api/v1/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: 'anthropic', model: 'claude-3-5-sonnet-20241022' })
      });
      if (res.ok) {
        const data = await res.json();
        const newSession: ChatSession = { id: data.id, provider: data.provider, model: data.model };
        setActiveSession(newSession);
        setMessages([]);
        localStorage.setItem('lenny_session_id', data.id);
      }
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
  };

  // Run Insight Search (Feature 2)
  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    setSearchHasRun(true);
    try {
      const res = await fetch(`/api/v1/search?query=${encodeURIComponent(searchQuery)}&limit=4`);
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  // Submit Chat Message and read stream (Feature 3/5)
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || !activeSession || chatLoading) return;

    const userMessageContent = chatInput;
    setChatInput('');
    setChatLoading(true);

    const userMsg: Message = { role: 'user', content: userMessageContent };
    setMessages(prev => [...prev, userMsg]);

    const assistantMsg: Message = { role: 'assistant', content: '', citations: [], loading: true };
    setMessages(prev => [...prev, assistantMsg]);

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSession.id,
          message: userMessageContent,
          provider: activeSession.provider,
          model: activeSession.model
        })
      });

      if (!response.ok) {
        throw new Error('Streaming failed');
      }

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let assistantContent = '';
      let citations: Citation[] = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (!part.trim()) continue;

          const lines = part.split('\n');
          let event = '';
          let dataStr = '';

          for (const line of lines) {
            if (line.startsWith('event:')) {
              event = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
              dataStr = line.substring(5).trim();
            }
          }

          if (event && dataStr) {
            try {
              const payload = JSON.parse(dataStr);
              if (event === 'citation') {
                citations = payload.citations || [];
                setMessages(prev => {
                  const copy = [...prev];
                  const idx = copy.length - 1;
                  copy[idx] = { ...copy[idx], citations };
                  return copy;
                });
              } else if (event === 'token') {
                assistantContent += payload.token;
                setMessages(prev => {
                  const copy = [...prev];
                  const idx = copy.length - 1;
                  copy[idx] = { ...copy[idx], content: assistantContent, loading: false };
                  return copy;
                });
              } else if (event.startsWith('artifact_')) {
                // Pipe stream directly to Artifact State Context
                processStreamEvent(event, payload);
              } else if (event === 'done') {
                setMessages(prev => {
                  const copy = [...prev];
                  const idx = copy.length - 1;
                  copy[idx] = { ...copy[idx], id: payload.message_id, loading: false };
                  return copy;
                });
              }
            } catch (err) {
              console.error('SSE JSON parse error:', err);
            }
          }
        }
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => {
        const copy = [...prev];
        const idx = copy.length - 1;
        copy[idx] = {
          role: 'assistant',
          content: 'I experienced an issue fetching the response stream. Please try again.',
          loading: false
        };
        return copy;
      });
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* LEFT CONTENT AREA */}
      <div 
        className="flex flex-col h-full overflow-hidden transition-all duration-75 relative bg-gradient-to-b from-slate-950 via-slate-900 to-indigo-950"
        style={{ width: isOpen ? `calc(100vw - ${sidebarWidth}px)` : '100vw' }}
      >
        {/* Workspace Header */}
        <header className="flex items-center justify-between px-6 py-4 bg-slate-900/60 backdrop-blur-md border-b border-slate-800/80 z-10 flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="bg-indigo-600/20 p-2 rounded-xl border border-indigo-500/20">
              <Sparkles className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-base font-black bg-gradient-to-r from-indigo-400 to-purple-300 bg-clip-text text-transparent">
                Lenny Growth Assistant
              </h1>
              <p className="text-[10px] text-slate-400 font-medium">Expert Growth Insights RAG</p>
            </div>
          </div>

          {/* Mode Tabs */}
          <div className="flex bg-slate-950/80 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'chat'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/10'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Chat</span>
            </button>
            <button
              onClick={() => setActiveTab('search')}
              className={`flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'search'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/10'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              <span>Search</span>
            </button>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            {activeTab === 'chat' && (
              <button
                onClick={handleNewChat}
                title="New Chat Session"
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700/80 border border-slate-700/50 rounded-lg text-xs font-bold text-slate-300 hover:text-white transition-all active:scale-95"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Chat</span>
              </button>
            )}
          </div>
        </header>

        {/* MAIN PANEL */}
        <div className="flex-1 overflow-hidden relative flex flex-col">
          {activeTab === 'search' ? (
            /* SEARCH PANEL */
            <div className="flex-1 overflow-y-auto p-6 md:p-10 flex flex-col items-center">
              <div className="max-w-2xl w-full text-center mt-6 mb-10">
                <h2 className="text-2xl font-black text-slate-100 tracking-tight mb-2">Transcript Index Search</h2>
                <p className="text-slate-400 text-sm">
                  Search raw insights and direct interview paragraphs from past Lenny's Podcast episodes.
                </p>
              </div>

              <form onSubmit={handleSearchSubmit} className="max-w-2xl w-full flex gap-3 mb-8">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Query guest strategies (e.g. Elena Verna retention loops...)"
                  className="flex-1 bg-slate-900/60 backdrop-blur-sm border border-slate-800 rounded-xl px-5 py-3.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm"
                />
                <button
                  type="submit"
                  disabled={searchLoading}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-6 py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-600/20 active:scale-95 disabled:opacity-50 disabled:active:scale-100 text-sm"
                >
                  {searchLoading ? 'Searching...' : 'Search'}
                </button>
              </form>

              <div className="max-w-2xl w-full space-y-4 pb-12">
                {searchLoading && (
                  <div className="flex flex-col items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500 mb-3"></div>
                    <p className="text-slate-400 text-xs">Querying semantic embedding index...</p>
                  </div>
                )}

                {!searchLoading && searchResults.map((res, i) => (
                  <div
                    key={i}
                    className="bg-slate-900/40 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 shadow-md hover:border-slate-700/60 transition-all duration-200"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 pb-2 border-b border-slate-800/40">
                      <div>
                        <span className="text-indigo-400 font-extrabold text-sm block sm:inline">{res.guest_name}</span>
                        <span className="text-slate-600 hidden sm:inline"> — </span>
                        <span className="text-slate-400 italic text-xs block sm:inline">{res.transcript_title}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {res.timestamp_start && (
                          <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                            {res.timestamp_start}
                          </span>
                        )}
                        <span className="text-[10px] font-mono bg-indigo-950/60 text-indigo-300 border border-indigo-900/60 px-2 py-0.5 rounded">
                          Sim: {res.similarity}
                        </span>
                      </div>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                      {res.content}
                    </p>
                  </div>
                ))}

                {!searchLoading && searchHasRun && searchResults.length === 0 && (
                  <div className="bg-slate-900/20 border border-dashed border-slate-800 rounded-xl py-12 text-center">
                    <p className="text-slate-500 text-sm">No matching insights found.</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* CHAT PANEL */
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Message Thread */}
              <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
                {messages.length === 0 && (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 mt-12 max-w-md mx-auto">
                    <Sparkles className="w-8 h-8 text-indigo-400 mb-4 animate-pulse" />
                    <h3 className="text-lg font-bold text-slate-200">How can Lenny assist you?</h3>
                    <p className="text-slate-400 text-xs mt-2 leading-relaxed">
                      Ask questions about growth loops, PM frameworks, retention, or onboarding strategies. 
                      Lenny will fetch citations and render documents/dashboards in the sandbox as required.
                    </p>
                  </div>
                )}

                {messages.map((msg, i) => {
                  const cleanedText = cleanArtifactTags(msg.content);
                  const parsedArts = extractArtifacts(msg.content);
                  
                  return (
                    <div 
                      key={i} 
                      className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                    >
                      {/* Bubble */}
                      <div 
                        className={`max-w-[85%] rounded-2xl p-4 shadow-md ${
                          msg.role === 'user'
                            ? 'bg-indigo-600 text-white rounded-br-none'
                            : 'bg-slate-900/80 border border-slate-850/80 rounded-bl-none text-slate-200'
                        }`}
                      >
                        {msg.loading && !cleanedText ? (
                          <div className="flex items-center space-x-2 py-1">
                            <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                          </div>
                        ) : (
                          <p className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
                            {cleanedText}
                          </p>
                        )}

                        {/* Artifact Cards */}
                        {parsedArts.map((art, idx) => (
                          <button
                            key={idx}
                            onClick={() => openArtifact({
                              artifact_key: art.key,
                              title: art.title,
                              type: art.type,
                              content: art.content,
                              version: 1,
                              session_id: activeSession?.id || ''
                            })}
                            className="mt-3 flex items-center justify-between p-3 bg-slate-950/80 hover:bg-slate-950 border border-slate-800 rounded-xl hover:border-indigo-500/50 transition-all text-left w-full group"
                          >
                            <div className="flex items-center space-x-3">
                              <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/10">
                                <BookOpen className="w-4 h-4" />
                              </div>
                              <div>
                                <p className="text-[10px] text-indigo-400 font-black uppercase tracking-wider">{art.type}</p>
                                <h4 className="text-xs font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">{art.title}</h4>
                              </div>
                            </div>
                            <div className="text-[10px] text-slate-400 flex items-center space-x-1 font-bold">
                              <span>Open Sandbox</span>
                              <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                            </div>
                          </button>
                        ))}
                      </div>

                      {/* Citations references */}
                      {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1.5 max-w-[85%]">
                          <span className="text-[10px] text-slate-500 flex items-center font-semibold uppercase tracking-wider mr-1">
                            Sources:
                          </span>
                          {msg.citations.map((cit, cIdx) => (
                            <button
                              key={cIdx}
                              onClick={() => setSelectedCitation(cit)}
                              className="text-[10px] bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 px-2 py-0.5 rounded transition-all flex items-center space-x-1"
                            >
                              <span>{cit.guest_name}</span>
                              <ExternalLink className="w-2.5 h-2.5 text-slate-500" />
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input Area */}
              <form onSubmit={handleChatSubmit} className="p-4 bg-slate-900/40 border-t border-slate-800/80 flex-shrink-0">
                <div className="flex items-center space-x-3 bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2">
                  <textarea
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleChatSubmit(e);
                      }
                    }}
                    placeholder="Ask Lenny anything... (Enter to send, Shift+Enter for new line)"
                    rows={1}
                    className="flex-1 bg-transparent border-0 text-slate-100 placeholder-slate-500 focus:ring-0 focus:outline-none text-sm resize-none py-1"
                  />
                  <button
                    type="submit"
                    disabled={!chatInput.trim() || chatLoading}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white p-2 rounded-lg transition-all shadow-md active:scale-95"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>

      {/* RESIZABLE DIVIDER DRAG HANDLE */}
      {isOpen && (
        <div 
          className={`w-[4px] cursor-col-resize hover:bg-indigo-500 transition-colors h-full flex-shrink-0 z-20 ${
            isResizing ? 'bg-indigo-600' : 'bg-slate-900 border-l border-slate-800'
          }`}
          onMouseDown={startResizing}
        />
      )}

      {/* RIGHT SIDEBAR VIEWPORT */}
      {isOpen && (
        <div 
          className="h-full flex-shrink-0 z-10"
          style={{ width: `${sidebarWidth}px` }}
        >
          <ArtifactViewer />
        </div>
      )}

      {/* CITATION MODAL DRAWER OVERLAY */}
      {selectedCitation && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg max-h-[80vh] flex flex-col shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between p-5 border-b border-slate-850">
              <div>
                <h3 className="text-md font-bold text-slate-100">{selectedCitation.guest_name}</h3>
                <p className="text-xs text-slate-400 italic mt-0.5">{selectedCitation.transcript_title}</p>
              </div>
              <button 
                onClick={() => setSelectedCitation(null)}
                className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="flex items-center space-x-2">
                {selectedCitation.speaker && (
                  <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                    Speaker: {selectedCitation.speaker}
                  </span>
                )}
                {selectedCitation.timestamp_start && (
                  <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                    Time: {selectedCitation.timestamp_start}
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap font-sans bg-slate-950/50 p-4 rounded-xl border border-slate-850">
                "{selectedCitation.content}"
              </p>
            </div>
            <div className="p-4 border-t border-slate-850 bg-slate-950/20 text-right">
              <button
                onClick={() => setSelectedCitation(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-bold rounded-lg transition-colors text-slate-200 hover:text-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function App() {
  return (
    <ArtifactProvider>
      <AppContent />
    </ArtifactProvider>
  );
}

export default App;
