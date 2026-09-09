import { useState, useMemo, useCallback, useRef } from 'react';
import { useChat } from '../../contexts/ChatContext';
import { useTheme } from '../../contexts/ThemeContext';
import { toast } from 'sonner';
import {
  Plus, Search, FileText, Trash2, Pencil, Check, X,
  Upload, Loader2, Sun, Moon, Monitor, Settings,
  ChevronLeft, Microscope
} from 'lucide-react';
import clsx from 'clsx';

// ── Date grouping helper ────────────────────────────────────────
function groupByDate(sessions) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  const weekAgo = new Date(today); weekAgo.setDate(today.getDate() - 7);

  const groups = { 'Today': [], 'Yesterday': [], 'Previous 7 Days': [], 'Older': [] };

  for (const s of sessions) {
    const d = s.created_at ? new Date(s.created_at) : null;
    if (!d || isNaN(d)) { groups['Older'].push(s); continue; }
    if (d >= today) groups['Today'].push(s);
    else if (d >= yesterday) groups['Yesterday'].push(s);
    else if (d >= weekAgo) groups['Previous 7 Days'].push(s);
    else groups['Older'].push(s);
  }
  return Object.entries(groups).filter(([, items]) => items.length > 0);
}

// ── Sidebar ─────────────────────────────────────────────────────
export default function Sidebar({ onClose, isOpen }) {
  const {
    sessionId, sessions, sessionsLoading, activeDocument,
    newChat, loadSession, removeSession, renameSessionTitle,
    ingestDocument, isIngesting,
  } = useChat();
  const { preference, setTheme } = useTheme();

  const [search, setSearch] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const fileInputRef = useRef(null);

  // Filter sessions
  const filtered = useMemo(() => {
    if (!search.trim()) return sessions;
    const q = search.toLowerCase();
    return sessions.filter(s => s.title?.toLowerCase().includes(q));
  }, [sessions, search]);

  const grouped = useMemo(() => groupByDate(filtered), [filtered]);

  // Handle file upload
  const handleFileChange = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await ingestDocument(file);
      if (result.status === 'success') {
        const { text_blocks, visuals_processed, cache_hits } = result.telemetry || {};
        toast.success(`Ingested: ${text_blocks} text blocks, ${visuals_processed} visuals (${cache_hits} cached)`);
      } else {
        toast.error(result.error || 'Ingestion failed');
      }
    } catch (err) {
      toast.error(`Upload failed: ${err.message}`);
    }
    e.target.value = '';
  }, [ingestDocument]);

  // Rename handlers
  const startRename = (s) => { setEditingId(s.session_id); setEditTitle(s.title); };
  const confirmRename = async () => {
    if (!editTitle.trim()) return;
    try {
      await renameSessionTitle(editingId, editTitle.trim());
      toast.success('Renamed');
    } catch { toast.error('Rename failed'); }
    setEditingId(null);
  };

  // Delete handlers
  const confirmDelete = async (sid) => {
    try {
      await removeSession(sid);
      toast.success('Conversation deleted');
    } catch { toast.error('Delete failed'); }
    setDeletingId(null);
  };

  const s = {
    container: {
      display: 'flex', flexDirection: 'column', height: '100%',
      padding: '12px', gap: '4px', overflow: 'hidden',
    },
    brand: {
      display: 'flex', alignItems: 'center', gap: '10px',
      padding: '8px 8px 12px', marginBottom: '4px',
    },
    brandIcon: {
      width: 32, height: 32, borderRadius: 'var(--radius-md)',
      background: 'var(--color-accent)', color: 'white',
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    },
    newChatBtn: {
      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
      width: '100%', padding: '10px', border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)', background: 'var(--color-bg-surface)',
      color: 'var(--color-text-primary)', cursor: 'pointer', fontWeight: 500,
      fontSize: '0.875rem', transition: 'background 0.15s',
    },
    searchBox: {
      display: 'flex', alignItems: 'center', gap: '8px',
      padding: '8px 10px', borderRadius: 'var(--radius-md)',
      background: 'var(--color-bg-elevated)', border: 'none', marginTop: '8px',
    },
    searchInput: {
      flex: 1, background: 'transparent', border: 'none', outline: 'none',
      color: 'var(--color-text-primary)', fontSize: '0.8125rem',
    },
    sectionLabel: {
      fontSize: '0.6875rem', fontWeight: 600, color: 'var(--color-text-tertiary)',
      textTransform: 'uppercase', letterSpacing: '0.05em',
      padding: '12px 8px 4px',
    },
    sessionItem: (isActive) => ({
      display: 'flex', alignItems: 'center', gap: '8px',
      padding: '8px 10px', borderRadius: 'var(--radius-md)',
      cursor: 'pointer', fontSize: '0.8125rem', position: 'relative',
      background: isActive ? 'var(--color-bg-elevated)' : 'transparent',
      color: 'var(--color-text-primary)',
      transition: 'background 0.1s',
    }),
    sessionTitle: {
      flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
    },
    hoverActions: {
      display: 'flex', gap: '2px', opacity: 0, transition: 'opacity 0.1s',
    },
    iconBtn: {
      background: 'none', border: 'none', padding: '4px',
      cursor: 'pointer', color: 'var(--color-text-secondary)',
      borderRadius: 'var(--radius-sm)', display: 'flex',
    },
    uploadArea: {
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px',
      padding: '16px', borderRadius: 'var(--radius-md)',
      border: '1px dashed var(--color-border)', cursor: 'pointer',
      background: 'var(--color-bg-surface)', textAlign: 'center',
      transition: 'border-color 0.15s',
    },
    footer: {
      marginTop: 'auto', paddingTop: '8px',
      borderTop: '1px solid var(--color-border)',
      display: 'flex', flexDirection: 'column', gap: '4px',
    },
    themeRow: {
      display: 'flex', gap: '4px', padding: '4px',
      background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)',
    },
    themeBtn: (isActive) => ({
      flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
      gap: '4px', padding: '6px', borderRadius: 'var(--radius-sm)',
      background: isActive ? 'var(--color-bg-surface)' : 'transparent',
      border: isActive ? '1px solid var(--color-border)' : '1px solid transparent',
      cursor: 'pointer', color: 'var(--color-text-primary)',
      fontSize: '0.75rem', fontWeight: isActive ? 500 : 400,
      boxShadow: isActive ? 'var(--shadow-sm)' : 'none',
    }),
  };

  return (
    <div style={s.container}>
      {/* Brand */}
      <div style={s.brand}>
        <div style={s.brandIcon}><Microscope size={18} /></div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '1rem' }}>Omni-STEM</div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-tertiary)' }}>AI STEM Workspace</div>
        </div>
      </div>

      {/* New Chat */}
      <button
        style={s.newChatBtn}
        onClick={newChat}
        onMouseEnter={e => e.target.style.background = 'var(--color-bg-hover)'}
        onMouseLeave={e => e.target.style.background = 'var(--color-bg-surface)'}
      >
        <Plus size={16} /> New Chat
      </button>

      {/* Search */}
      <div style={s.searchBox}>
        <Search size={14} style={{ color: 'var(--color-text-tertiary)', flexShrink: 0 }} />
        <input
          style={s.searchInput}
          placeholder="Search conversations…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          aria-label="Search conversations"
        />
      </div>

      {/* Session List */}
      <div style={{ flex: 1, overflowY: 'auto', marginTop: '4px' }}>
        {sessionsLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '24px' }}>
            <Loader2 size={18} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-text-tertiary)' }} />
          </div>
        ) : grouped.length === 0 ? (
          <div style={{ padding: '24px 12px', textAlign: 'center', color: 'var(--color-text-tertiary)', fontSize: '0.8125rem' }}>
            {search ? 'No matches found' : 'No conversations yet'}
          </div>
        ) : (
          grouped.map(([label, items]) => (
            <div key={label}>
              <div style={s.sectionLabel}>{label}</div>
              {items.map(sess => {
                const isActive = sess.session_id === sessionId;
                const isEditing = editingId === sess.session_id;
                const isDeleting = deletingId === sess.session_id;

                return (
                  <div
                    key={sess.session_id}
                    style={s.sessionItem(isActive)}
                    onClick={() => { if (!isEditing && !isDeleting) loadSession(sess.session_id); }}
                    onMouseEnter={e => {
                      if (!isActive) e.currentTarget.style.background = 'var(--color-bg-hover)';
                      const actions = e.currentTarget.querySelector('[data-actions]');
                      if (actions) actions.style.opacity = '1';
                    }}
                    onMouseLeave={e => {
                      if (!isActive) e.currentTarget.style.background = 'transparent';
                      const actions = e.currentTarget.querySelector('[data-actions]');
                      if (actions) actions.style.opacity = '0';
                    }}
                  >
                    <FileText size={14} style={{ flexShrink: 0, color: 'var(--color-text-tertiary)' }} />

                    {isEditing ? (
                      <input
                        value={editTitle}
                        onChange={e => setEditTitle(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter') confirmRename(); if (e.key === 'Escape') setEditingId(null); }}
                        autoFocus
                        onClick={e => e.stopPropagation()}
                        style={{
                          flex: 1, background: 'var(--color-bg-surface)', border: '1px solid var(--color-accent)',
                          borderRadius: '4px', padding: '2px 6px', color: 'var(--color-text-primary)',
                          fontSize: '0.8125rem', outline: 'none',
                        }}
                      />
                    ) : isDeleting ? (
                      <span style={{ flex: 1, fontSize: '0.75rem', color: 'var(--color-error)' }}>Delete?</span>
                    ) : (
                      <span style={s.sessionTitle}>{sess.title || 'Untitled'}</span>
                    )}

                    {isEditing ? (
                      <div style={{ display: 'flex', gap: '2px' }}>
                        <button style={s.iconBtn} onClick={e => { e.stopPropagation(); confirmRename(); }}><Check size={14} /></button>
                        <button style={s.iconBtn} onClick={e => { e.stopPropagation(); setEditingId(null); }}><X size={14} /></button>
                      </div>
                    ) : isDeleting ? (
                      <div style={{ display: 'flex', gap: '2px' }}>
                        <button style={{...s.iconBtn, color: 'var(--color-error)'}} onClick={e => { e.stopPropagation(); confirmDelete(sess.session_id); }}><Check size={14} /></button>
                        <button style={s.iconBtn} onClick={e => { e.stopPropagation(); setDeletingId(null); }}><X size={14} /></button>
                      </div>
                    ) : (
                      <div data-actions style={s.hoverActions}>
                        <button style={s.iconBtn} onClick={e => { e.stopPropagation(); startRename(sess); }} title="Rename"><Pencil size={13} /></button>
                        <button style={s.iconBtn} onClick={e => { e.stopPropagation(); setDeletingId(sess.session_id); }} title="Delete"><Trash2 size={13} /></button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))
        )}
      </div>

      {/* Upload */}
      <div style={{ padding: '4px 0' }}>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.png,.jpg,.jpeg"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        <div
          style={s.uploadArea}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={e => { e.preventDefault(); e.currentTarget.style.borderColor = 'var(--color-accent)'; }}
          onDragLeave={e => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
          onDrop={e => {
            e.preventDefault();
            e.currentTarget.style.borderColor = 'var(--color-border)';
            const file = e.dataTransfer.files[0];
            if (file) {
              const fakeEvent = { target: { files: [file], value: '' } };
              handleFileChange(fakeEvent);
            }
          }}
        >
          {isIngesting ? (
            <>
              <Loader2 size={20} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-accent)' }} />
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>Processing…</span>
            </>
          ) : (
            <>
              <Upload size={18} style={{ color: 'var(--color-text-tertiary)' }} />
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                {activeDocument ? `Replace ${activeDocument}` : 'Upload PDF, DOCX, or Image'}
              </span>
            </>
          )}
        </div>
        {activeDocument && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '6px 8px', marginTop: '6px', borderRadius: 'var(--radius-sm)',
            background: 'var(--color-success-bg)', fontSize: '0.75rem',
            color: 'var(--color-success)',
          }}>
            <FileText size={13} /> {activeDocument}
          </div>
        )}
      </div>

      {/* Footer: Theme switcher */}
      <div style={s.footer}>
        <div style={s.themeRow}>
          <button style={s.themeBtn(preference === 'light')} onClick={() => setTheme('light')}>
            <Sun size={13} /> Light
          </button>
          <button style={s.themeBtn(preference === 'dark')} onClick={() => setTheme('dark')}>
            <Moon size={13} /> Dark
          </button>
          <button style={s.themeBtn(preference === 'system')} onClick={() => setTheme('system')}>
            <Monitor size={13} /> Auto
          </button>
        </div>
        <div style={{ textAlign: 'center', fontSize: '0.625rem', color: 'var(--color-text-tertiary)', padding: '4px' }}>
          Omni-STEM v1.0
        </div>
      </div>
    </div>
  );
}
