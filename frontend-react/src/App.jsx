import { Toaster } from 'sonner';
import { ThemeProvider } from './contexts/ThemeContext';
import { ChatProvider } from './contexts/ChatContext';
import { AccessibilityProvider } from './contexts/AccessibilityContext';
import AppShell from './components/layout/AppShell';
import './index.css';

export default function App() {
  return (
    <AccessibilityProvider>
      <ThemeProvider>
        <ChatProvider>
          <AppShell />
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: 'var(--color-bg-surface)',
                color: 'var(--color-text-primary)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.875rem',
              },
            }}
          />
        </ChatProvider>
      </ThemeProvider>
    </AccessibilityProvider>
  );
}
