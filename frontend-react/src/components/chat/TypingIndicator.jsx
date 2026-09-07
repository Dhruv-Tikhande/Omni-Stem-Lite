export default function TypingIndicator() {
  return (
    <div style={{ display: 'flex', gap: '12px', padding: '16px 24px' }}>
      <div style={{
        width: 28, height: 28, borderRadius: 'var(--radius-md)',
        background: 'var(--color-accent-subtle)', color: 'var(--color-accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L12 6M12 18L12 22M4.93 4.93L7.76 7.76M16.24 16.24L19.07 19.07M2 12L6 12M18 12L22 12M4.93 19.07L7.76 16.24M16.24 7.76L19.07 4.93" /></svg>
      </div>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '6px',
        padding: '12px 16px', borderRadius: 'var(--radius-md)',
        background: 'var(--color-bg-elevated)',
      }}>
        {[0, 1, 2].map(i => (
          <div
            key={i}
            style={{
              width: 7, height: 7, borderRadius: '50%',
              background: 'var(--color-text-tertiary)',
              animation: `pulse-dot 1.4s ease-in-out ${i * 0.2}s infinite`,
            }}
          />
        ))}
      </div>
    </div>
  );
}
