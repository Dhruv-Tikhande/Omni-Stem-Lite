import { Microscope, BookOpen, Calculator, FlaskConical, HelpCircle, ListChecks } from 'lucide-react';

const suggestions = [
  { icon: BookOpen, text: 'Summarize this document', color: '#6366f1' },
  { icon: HelpCircle, text: 'Explain this concept simply', color: '#8b5cf6' },
  { icon: Calculator, text: 'Solve this problem step by step', color: '#06b6d4' },
  { icon: FlaskConical, text: 'Find the important formulas', color: '#10b981' },
  { icon: ListChecks, text: 'Create practice questions', color: '#f59e0b' },
];

export default function WelcomeScreen({ onSend }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', height: '100%', padding: '40px 24px',
      textAlign: 'center',
    }}>
      <div style={{
        width: 56, height: 56, borderRadius: 'var(--radius-lg)',
        background: 'var(--color-accent-subtle)', color: 'var(--color-accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: '20px',
      }}>
        <Microscope size={28} />
      </div>

      <h1 style={{
        fontSize: '1.75rem', fontWeight: 700,
        color: 'var(--color-text-primary)',
        marginBottom: '8px', letterSpacing: '-0.02em',
      }}>
        Omni-STEM
      </h1>

      <p style={{
        fontSize: '0.95rem', color: 'var(--color-text-secondary)',
        maxWidth: '420px', lineHeight: 1.5, marginBottom: '36px',
      }}>
        Your AI-powered STEM workspace. Upload a document, diagram, or image and start learning.
      </p>

      <div style={{
        display: 'flex', flexWrap: 'wrap', gap: '10px',
        justifyContent: 'center', maxWidth: '560px',
      }}>
        {suggestions.map((s, i) => (
          <button
            key={i}
            onClick={() => onSend(s.text)}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '10px 16px', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              background: 'var(--color-bg-surface)',
              color: 'var(--color-text-primary)',
              cursor: 'pointer', fontSize: '0.8125rem',
              transition: 'all 0.15s',
              fontFamily: 'inherit',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = s.color;
              e.currentTarget.style.background = 'var(--color-bg-elevated)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = 'var(--color-border)';
              e.currentTarget.style.background = 'var(--color-bg-surface)';
            }}
          >
            <s.icon size={15} style={{ color: s.color, flexShrink: 0 }} />
            {s.text}
          </button>
        ))}
      </div>

      <p style={{
        marginTop: '40px', fontSize: '0.75rem',
        color: 'var(--color-text-tertiary)',
      }}>
        Upload a PDF, DOCX, or image in the sidebar to get started
      </p>
    </div>
  );
}
