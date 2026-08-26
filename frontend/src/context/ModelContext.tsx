import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export type ProviderType = 'ollama' | 'anthropic' | 'groq';

export interface ModelInfo {
  id: string;
  name: string;
  provider: ProviderType;
  status: 'online' | 'offline' | 'degraded';
  pingMs?: number;
}

interface ModelContextType {
  selectedProvider: ProviderType;
  selectedModel: string;
  models: ModelInfo[];
  isOllamaOfflineModalOpen: boolean;
  setIsOllamaOfflineModalOpen: (open: boolean) => void;
  selectProvider: (provider: ProviderType) => void;
  selectModel: (modelId: string) => void;
  checkHealth: () => Promise<void>;
  healthStatus: Record<ProviderType, boolean>;
}

const ModelContext = createContext<ModelContextType | undefined>(undefined);

const DEFAULT_MODELS: ModelInfo[] = [
  { id: 'llama3.2', name: 'Local Ollama (Llama 3.2)', provider: 'ollama', status: 'online' },
  { id: 'claude-3-5-sonnet-20241022', name: 'Anthropic Claude 3.5 Sonnet', provider: 'anthropic', status: 'online' },
  { id: 'llama-3.3-70b-versatile', name: 'Groq Llama 3.3 70B', provider: 'groq', status: 'online' },
];

export const ModelProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedProvider, setSelectedProvider] = useState<ProviderType>('anthropic');
  const [selectedModel, setSelectedModel] = useState<string>('claude-3-5-sonnet-20241022');
  const [models] = useState<ModelInfo[]>(DEFAULT_MODELS);
  const [isOllamaOfflineModalOpen, setIsOllamaOfflineModalOpen] = useState<boolean>(false);
  const [healthStatus, setHealthStatus] = useState<Record<ProviderType, boolean>>({
    ollama: false,
    anthropic: true,
    groq: true,
  });

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/models/providers');
      if (res.ok) {
        const data = await res.json();
        const apiProviders = data.providers || [];
        const statusMap: Record<ProviderType, boolean> = {
          ollama: false,
          anthropic: false,
          groq: false,
        };
        apiProviders.forEach((p: any) => {
          if (p.provider_name in statusMap) {
            statusMap[p.provider_name as ProviderType] = p.status === 'online';
          }
        });
        setHealthStatus(statusMap);
      }
    } catch {
      // Fallback polling for backend connection check
      try {
        const ollamaCheck = await fetch('http://localhost:11434/api/version', { method: 'GET' }).catch(() => null);
        setHealthStatus({
          ollama: !!ollamaCheck && ollamaCheck.ok,
          anthropic: true,
          groq: true,
        });
      } catch {
        setHealthStatus((prev) => ({ ...prev, ollama: false }));
      }
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const selectProvider = (provider: ProviderType) => {
    if (provider === 'ollama' && !healthStatus.ollama) {
      setIsOllamaOfflineModalOpen(true);
      return;
    }
    setSelectedProvider(provider);
    const firstModel = models.find((m) => m.provider === provider);
    if (firstModel) {
      setSelectedModel(firstModel.id);
    }
  };

  const selectModel = (modelId: string) => {
    setSelectedModel(modelId);
    const target = models.find((m) => m.id === modelId);
    if (target) {
      setSelectedProvider(target.provider);
    }
  };

  return (
    <ModelContext.Provider
      value={{
        selectedProvider,
        selectedModel,
        models,
        isOllamaOfflineModalOpen,
        setIsOllamaOfflineModalOpen,
        selectProvider,
        selectModel,
        checkHealth,
        healthStatus,
      }}
    >
      {children}
    </ModelContext.Provider>
  );
};

export const useModel = () => {
  const ctx = useContext(ModelContext);
  if (!ctx) throw new Error('useModel must be used within ModelProvider');
  return ctx;
};
