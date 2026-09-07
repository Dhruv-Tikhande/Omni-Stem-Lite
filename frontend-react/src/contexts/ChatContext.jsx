import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import * as api from '../services/api';

const ChatContext = createContext();

const STORAGE_KEY = 'omni-stem-session-id';

export function ChatProvider({ children }) {
  const [sessionId, setSessionId] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY) || uuidv4(); }
    catch { return uuidv4(); }
  });
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [activeDocument, setActiveDocument] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const abortRef = useRef(null);

  // Persist sessionId
  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, sessionId); } catch {}
  }, [sessionId]);

  // Load sessions list
  const refreshSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const list = await api.fetchSessions();
      setSessions(list);
    } catch {
      setSessions([]);
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => { refreshSessions(); }, [refreshSessions]);

  // Load a specific session
  const loadSession = useCallback(async (sid) => {
    try {
      const data = await api.fetchSession(sid);
      setSessionId(sid);
      setMessages(data.messages || []);
      setActiveDocument(data.title && data.title !== 'New Chat' ? data.title : null);
    } catch (err) {
      console.error('Failed to load session:', err);
    }
  }, []);

  // New chat
  const newChat = useCallback(() => {
    const newId = uuidv4();
    setSessionId(newId);
    setMessages([]);
    setActiveDocument(null);
  }, []);

  // Delete session
  const removeSession = useCallback(async (sid) => {
    try {
      await api.deleteSession(sid);
      setSessions(prev => prev.filter(s => s.session_id !== sid));
      if (sid === sessionId) newChat();
    } catch (err) {
      console.error('Failed to delete session:', err);
      throw err;
    }
  }, [sessionId, newChat]);

  // Rename session
  const renameSessionTitle = useCallback(async (sid, title) => {
    try {
      await api.renameSession(sid, title);
      setSessions(prev => prev.map(s => s.session_id === sid ? { ...s, title } : s));
      if (sid === sessionId && activeDocument) setActiveDocument(title);
    } catch (err) {
      console.error('Failed to rename session:', err);
      throw err;
    }
  }, [sessionId, activeDocument]);

  // Ingest document
  const ingestDocument = useCallback(async (file) => {
    setIsIngesting(true);
    try {
      const result = await api.ingestDocument(file, sessionId);
      if (result.success) {
        setActiveDocument(file.name);
        setMessages([{
          role: 'assistant',
          content: `📄 I've finished processing **${file.name}**. ${result.summary} Ask me anything about it!`,
        }]);
        await refreshSessions();
      }
      return result;
    } finally {
      setIsIngesting(false);
    }
  }, [sessionId, refreshSessions]);

  // Send chat message
  const sendMessage = useCallback(async (text) => {
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await api.sendChatMessage(sessionId, text);
      const assistantMsg = {
        role: 'assistant',
        content: data.response,
        latency: data.latency_seconds,
        contextFound: data.context_found,
      };
      setMessages(prev => [...prev, assistantMsg]);
      await refreshSessions();
      return assistantMsg;
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: `I couldn't get a response. ${err.message}`,
        isError: true,
      };
      setMessages(prev => [...prev, errorMsg]);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, refreshSessions]);

  // Regenerate last response
  const regenerateLastResponse = useCallback(async () => {
    const lastUserIdx = messages.map(m => m.role).lastIndexOf('user');
    if (lastUserIdx === -1) return;
    const lastUserMsg = messages[lastUserIdx].content;
    // Remove last assistant message
    setMessages(prev => prev.slice(0, -1));
    setIsLoading(true);
    try {
      const data = await api.sendChatMessage(sessionId, lastUserMsg);
      const assistantMsg = {
        role: 'assistant',
        content: data.response,
        latency: data.latency_seconds,
        contextFound: data.context_found,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Regeneration failed: ${err.message}`, isError: true }]);
    } finally {
      setIsLoading(false);
    }
  }, [messages, sessionId]);

  const value = {
    sessionId,
    messages,
    setMessages,
    sessions,
    sessionsLoading,
    activeDocument,
    isLoading,
    isIngesting,
    newChat,
    loadSession,
    removeSession,
    renameSessionTitle,
    ingestDocument,
    sendMessage,
    regenerateLastResponse,
    refreshSessions,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used within ChatProvider');
  return ctx;
}
