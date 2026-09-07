import { useChat } from '../../contexts/ChatContext';
import { PanelLeftClose, PanelLeftOpen, FileText } from 'lucide-react';

export default function ChatHeader({ onToggleSidebar, sidebarOpen }) {
  const { activeDocument, sessionId } = useChat();

  return (
    <div
      className="hidden md:flex"
      style={{
        alignItems: 'center',
        gap: '12px',
        padding: '10px 20px',
        borderBottom: '1px solid var(--color-border)',
        background: 'var(--color-bg-surface)',
        flexShrink: 0,
      }}
    >
      <button
        onClick={onToggleSidebar}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--color-text-secondary)',
          padding: '4px',
          display: 'flex',
          borderRadius: 'var(--radius-sm)',
        }}
        aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
        title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
      >
        {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
      </button>

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Omni-STEM</span>
        {activeDocument && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '5px',
            padding: '3px 10px', borderRadius: 'var(--radius-full)',
            background: 'var(--color-accent-subtle)',
            color: 'var(--color-accent)', fontSize: '0.75rem', fontWeight: 500,
          }}>
            <FileText size={12} />
            {activeDocument}
          </div>
        )}
      </div>
    </div>
  );
}
