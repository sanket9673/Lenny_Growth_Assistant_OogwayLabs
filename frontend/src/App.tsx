
import { SessionProvider } from './context/SessionContext';
import { ModelProvider } from './context/ModelContext';
import { ChatProvider } from './context/ChatContext';
import { ArtifactProvider } from './context/ArtifactContext';
import { AppLayout } from './components/layout/AppLayout';

export function App() {
  return (
    <SessionProvider>
      <ModelProvider>
        <ArtifactProvider>
          <ChatProvider>
            <AppLayout />
          </ChatProvider>
        </ArtifactProvider>
      </ModelProvider>
    </SessionProvider>
  );
}

export default App;
