import { useRef, useEffect } from 'react';
import { useChat } from '../../contexts/ChatContext';
import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import ChatComposer from './ChatComposer';
import WelcomeScreen from './WelcomeScreen';

export default function ChatWorkspace({ onToggleSidebar, sidebarOpen }) {
  const { messages, isLoading, sendMessage, activeDocument } = useChat();
  const scrollRef = useRef(null);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  const hasMessages = messages.length > 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
      <ChatHeader
        onToggleSidebar={onToggleSidebar}
        sidebarOpen={sidebarOpen}
      />

      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
        }}
      >
        {hasMessages ? (
          <MessageList messages={messages} isLoading={isLoading} />
        ) : (
          <WelcomeScreen onSend={sendMessage} />
        )}
      </div>

      <ChatComposer />
    </div>
  );
}
