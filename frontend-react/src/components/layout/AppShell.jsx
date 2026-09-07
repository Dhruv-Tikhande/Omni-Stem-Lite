import { useState } from 'react';
import Sidebar from './Sidebar';
import ChatWorkspace from '../chat/ChatWorkspace';
import { Menu } from 'lucide-react';

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Desktop Sidebar */}
      <div
        style={{
          width: sidebarOpen ? 'var(--sidebar-width)' : '0px',
          minWidth: sidebarOpen ? 'var(--sidebar-width)' : '0px',
          transition: 'width 0.2s ease, min-width 0.2s ease',
          overflow: 'hidden',
          borderRight: sidebarOpen ? '1px solid var(--color-border)' : 'none',
          background: 'var(--color-bg-sidebar)',
          flexShrink: 0,
        }}
        className="hidden md:block"
      >
        <Sidebar
          onClose={() => setSidebarOpen(false)}
          isOpen={sidebarOpen}
        />
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileSidebarOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 50,
            display: 'flex',
          }}
          className="md:hidden"
        >
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'var(--color-overlay)',
            }}
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div
            style={{
              position: 'relative',
              width: 'var(--sidebar-width)',
              background: 'var(--color-bg-sidebar)',
              height: '100%',
              animation: 'slideInLeft 0.2s ease',
              zIndex: 51,
            }}
          >
            <Sidebar
              onClose={() => setMobileSidebarOpen(false)}
              isOpen={true}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        {/* Mobile header */}
        <div
          className="md:hidden"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '10px 16px',
            borderBottom: '1px solid var(--color-border)',
            background: 'var(--color-bg-surface)',
          }}
        >
          <button
            onClick={() => setMobileSidebarOpen(true)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-text-primary)',
              cursor: 'pointer',
              padding: '4px',
            }}
            aria-label="Open sidebar"
          >
            <Menu size={20} />
          </button>
          <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Omni-STEM</span>
        </div>

        <ChatWorkspace
          onToggleSidebar={() => setSidebarOpen(prev => !prev)}
          sidebarOpen={sidebarOpen}
        />
      </div>
    </div>
  );
}
