import { User } from 'lucide-react';

export default function UserMessage({ content, index }) {
  return (
    <div style={{ display: 'flex', gap: '12px', padding: '16px 24px', justifyContent: 'flex-end' }}>
      <div
        style={{
          maxWidth: '85%',
          padding: '12px 16px',
          borderRadius: '18px 18px 4px 18px',
          background: 'var(--color-user-bubble)',
          color: 'var(--color-user-text)',
          fontSize: '0.9rem',
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {content}
      </div>
    </div>
  );
}
