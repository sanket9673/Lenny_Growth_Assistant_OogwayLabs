import React, { useState } from 'react';
import { ArtifactSandbox } from './ArtifactSandbox';
import { MarkdownArtifact } from './MarkdownArtifact';
import { useArtifacts } from '../../context/ArtifactContext';

export const ArtifactViewer: React.FC = () => {
  const { activeArtifact, artifactHistory, selectVersion, closeArtifact, isOpen } = useArtifacts();
  const [activeTab, setActiveTab] = useState<'preview' | 'code'>('preview');
  const [copied, setCopied] = useState(false);

  if (!isOpen || !activeArtifact) return null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(activeArtifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const extMap: Record<string, string> = { html: 'html', markdown: 'md', svg: 'svg' };
    const extension = extMap[activeArtifact.type] || 'txt';
    const blob = new Blob([activeArtifact.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeArtifact.artifact_key}_v${activeArtifact.version}.${extension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-50 border-l border-slate-200 shadow-xl">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200">
        <div className="flex items-center space-x-3 truncate">
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200">
            {activeArtifact.type}
          </span>
          <h2 className="text-sm font-bold text-slate-800 truncate" title={activeArtifact.title}>
            {activeArtifact.title}
          </h2>
        </div>

        <div className="flex items-center space-x-2">
          {/* Version Selector */}
          {artifactHistory.length > 1 && (
            <select
              value={activeArtifact.version}
              onChange={(e) => selectVersion(Number(e.target.value))}
              className="text-xs border border-slate-300 rounded px-2 py-1 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {artifactHistory.map((item) => (
                <option key={item.id || item.version} value={item.version}>
                  v{item.version} {item.version === activeArtifact.version ? '(current)' : ''}
                </option>
              ))}
            </select>
          )}

          {/* Preview vs Code Tab */}
          <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200">
            <button
              onClick={() => setActiveTab('preview')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                activeTab === 'preview' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Preview
            </button>
            <button
              onClick={() => setActiveTab('code')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                activeTab === 'code' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Code
            </button>
          </div>

          {/* Download Button */}
          <button
            onClick={handleDownload}
            title="Download File"
            className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>

          {/* Copy Button */}
          <button
            onClick={handleCopy}
            title="Copy Code"
            className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
          >
            {copied ? (
              <span className="text-xs font-bold text-emerald-600">Copied!</span>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
              </svg>
            )}
          </button>

          {/* Close Panel Button */}
          <button
            onClick={closeArtifact}
            title="Close Panel"
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Main Content Pane */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab === 'preview' ? (
          activeArtifact.type === 'markdown' ? (
            <MarkdownArtifact content={activeArtifact.content} />
          ) : (
            <ArtifactSandbox content={activeArtifact.content} type={activeArtifact.type} title={activeArtifact.title} />
          )
        ) : (
          <div className="w-full h-full bg-slate-900 overflow-auto p-4">
            <pre className="text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed">
              <code>{activeArtifact.content}</code>
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
