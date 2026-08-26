import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useModel } from '../../context/ModelContext';
import { Terminal, Copy, Check, AlertTriangle, ArrowRight, X } from 'lucide-react';

export const OllamaSetupModal: React.FC = () => {
  const { isOllamaOfflineModalOpen, setIsOllamaOfflineModalOpen, selectProvider } = useModel();
  const [copied, setCopied] = useState(false);
  const command = 'ollama run llama3.2';

  const handleCopy = () => {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFallback = () => {
    setIsOllamaOfflineModalOpen(false);
    selectProvider('groq');
  };

  return (
    <Dialog.Root open={isOllamaOfflineModalOpen} onOpenChange={setIsOllamaOfflineModalOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 animate-in fade-in-0" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-2xl border border-slate-200 dark:border-slate-800 z-50 animate-in fade-in-0 zoom-in-95">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <Dialog.Title className="text-base font-semibold text-slate-900 dark:text-slate-100">
                  Ollama Offline
                </Dialog.Title>
                <Dialog.Description className="text-xs text-slate-500 dark:text-slate-400">
                  Local instance not detected on port 11434.
                </Dialog.Description>
              </div>
            </div>
            <Dialog.Close className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
              <X className="w-4 h-4" />
            </Dialog.Close>
          </div>

          <div className="mt-4 space-y-3">
            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              To use local inference, ensure Ollama is installed and running locally with your target model initialized.
            </p>

            <div className="bg-slate-950 text-slate-100 p-3 rounded-xl font-mono text-xs flex items-center justify-between border border-slate-800">
              <div className="flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-orange-400" />
                <span>{command}</span>
              </div>
              <button
                type="button"
                onClick={handleCopy}
                className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                title="Copy command"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          <div className="mt-6 flex flex-col sm:flex-row items-center justify-end gap-2">
            <button
              type="button"
              onClick={handleFallback}
              className="w-full sm:w-auto flex items-center justify-center space-x-1.5 px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 text-white text-xs font-medium transition-colors shadow-sm"
            >
              <span>Fallback to Cloud (Groq)</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
