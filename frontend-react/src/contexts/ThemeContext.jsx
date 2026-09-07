import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const ThemeContext = createContext();

const STORAGE_KEY = 'omni-stem-theme';

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function resolveTheme(preference) {
  if (preference === 'system') return getSystemTheme();
  return preference;
}

export function ThemeProvider({ children }) {
  const [preference, setPreference] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY) || 'dark'; }
    catch { return 'dark'; }
  });

  const resolved = resolveTheme(preference);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolved);
    try { localStorage.setItem(STORAGE_KEY, preference); } catch {}
  }, [preference, resolved]);

  // Listen for system theme changes when preference is 'system'
  useEffect(() => {
    if (preference !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => document.documentElement.setAttribute('data-theme', getSystemTheme());
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [preference]);

  const setTheme = useCallback((t) => setPreference(t), []);

  return (
    <ThemeContext.Provider value={{ theme: resolved, preference, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
