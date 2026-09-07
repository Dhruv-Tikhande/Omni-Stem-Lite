import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Copy, RefreshCw, Volume2, Microscope, AlertCircle } from 'lucide-react';
import { useChat } from '../../contexts/ChatContext';
import MarkdownRenderer from './MarkdownRenderer';
import AudioPlayer from '../voice/AudioPlayer';
import * as api from '../../services/api';

export default function AssistantMessage({ content, latency, isError, isLatest }) {
  const { regenerateLastResponse } = useChat();
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioLoading, setAudioLoading] = useState(false);
  const [hovering, setHovering] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('Copied to clipboard');
    } catch {
      toast.error('Failed to copy');
    }
  }, [content]);

  const handleReadAloud = useCallback(async () => {
    if (audioUrl) { setAudioUrl(null); return; }
    setAudioLoading(true);
    try {
      const url = await api.textToSpeech(content);
      setAudioUrl(url);
    } catch {
      toast.error('Text-to-speech unavailable');
    } finally {
      setAudioLoading(false);
    }
  }, [content, audioUrl]);

  const s = {
    wrapper: {
      display: 'flex', gap: '12px', padding: '16px 24px',
    },
    avatar: {
      width: 28, height: 28, borderRadius: 'var(--radius-md)',
      background: isError ? 'var(--color-error-bg)' : 'var(--color-accent-subtle)',
      color: isError ? 'var(--color-error)' : 'var(--color-accent)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0, marginTop: '2px',
    },
    body: {
      flex: 1, minWidth: 0,
    },
    actions: {
      display: 'flex', gap: '2px', marginTop: '8px',
      opacity: hovering ? 1 : 0, transition: 'opacity 0.15s',
    },
    actionBtn: {
      display: 'flex', alignItems: 'center', gap: '4px',
      padding: '4px 8px', borderRadius: 'var(--radius-sm)',
      background: 'none', border: 'none', cursor: 'pointer',
      color: 'var(--color-text-tertiary)', fontSize: '0.75rem',
      transition: 'color 0.1s, background 0.1s',
    },
    meta: {
      fontSize: '0.6875rem', color: 'var(--color-text-tertiary)',
      marginTop: '6px',
    },
  };

  return (
    <div
      style={s.wrapper}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
    >
      <div style={s.avatar}>
        {isError ? <AlertCircle size={15} /> : <Microscope size={15} />}
      </div>
      <div style={s.body}>
        <div className="markdown-content">
          <MarkdownRenderer content={content} />
        </div>

        {audioUrl && <AudioPlayer src={audioUrl} autoPlay={isLatest} />}

        {latency != null && (
          <div style={s.meta}>⏱ {latency}s</div>
        )}

        <div style={s.actions}>
          <button
            style={s.actionBtn}
            onClick={handleCopy}
            onMouseEnter={e => { e.target.style.color = 'var(--color-text-primary)'; e.target.style.background = 'var(--color-bg-elevated)'; }}
            onMouseLeave={e => { e.target.style.color = 'var(--color-text-tertiary)'; e.target.style.background = 'none'; }}
            title="Copy"
          >
            <Copy size={13} /> Copy
          </button>
          {isLatest && !isError && (
            <button
              style={s.actionBtn}
              onClick={regenerateLastResponse}
              onMouseEnter={e => { e.target.style.color = 'var(--color-text-primary)'; e.target.style.background = 'var(--color-bg-elevated)'; }}
              onMouseLeave={e => { e.target.style.color = 'var(--color-text-tertiary)'; e.target.style.background = 'none'; }}
              title="Regenerate"
            >
              <RefreshCw size={13} /> Regenerate
            </button>
          )}
          <button
            style={s.actionBtn}
            onClick={handleReadAloud}
            onMouseEnter={e => { e.target.style.color = 'var(--color-text-primary)'; e.target.style.background = 'var(--color-bg-elevated)'; }}
            onMouseLeave={e => { e.target.style.color = 'var(--color-text-tertiary)'; e.target.style.background = 'none'; }}
            title="Read aloud"
          >
            <Volume2 size={13} /> {audioLoading ? 'Loading…' : audioUrl ? 'Stop' : 'Read aloud'}
          </button>
        </div>
      </div>
    </div>
  );
}
