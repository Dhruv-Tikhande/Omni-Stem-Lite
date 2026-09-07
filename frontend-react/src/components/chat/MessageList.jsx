import UserMessage from './UserMessage';
import AssistantMessage from './AssistantMessage';
import TypingIndicator from './TypingIndicator';

export default function MessageList({ messages, isLoading }) {
  return (
    <div style={{ padding: '20px 0', maxWidth: 'var(--message-max-width)', margin: '0 auto', width: '100%' }}>
      {messages.map((msg, idx) => (
        <div
          key={idx}
          style={{ animation: 'fadeIn 0.3s ease', animationFillMode: 'both', animationDelay: `${Math.min(idx * 0.03, 0.3)}s` }}
        >
          {msg.role === 'user' ? (
            <UserMessage content={msg.content} index={idx} />
          ) : (
            <AssistantMessage
              content={msg.content}
              latency={msg.latency}
              isError={msg.isError}
              isLatest={idx === messages.length - 1}
            />
          )}
        </div>
      ))}
      {isLoading && <TypingIndicator />}
    </div>
  );
}
