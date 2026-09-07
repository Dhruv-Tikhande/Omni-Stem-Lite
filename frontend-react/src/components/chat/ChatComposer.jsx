import { useState, useRef, useCallback, useEffect } from 'react';
import { useChat } from '../../contexts/ChatContext';
import { toast } from 'sonner';
import { Send, Paperclip, Mic, MicOff, Loader2, X } from 'lucide-react';
import * as api from '../../services/api';

export default function ChatComposer() {
  const { sendMessage, isLoading, ingestDocument, activeDocument } = useChat();
  const [text, setText] = useState('');
  const [recording, setRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
  }, [text]);

  const handleSend = useCallback(async () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    setText('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    try {
      await sendMessage(trimmed);
    } catch {}
  }, [text, isLoading, sendMessage]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // File attachment
  const handleFileAttach = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await ingestDocument(file);
      if (result.success) toast.success(`${file.name} ingested`);
      else toast.error(result.error || 'Failed');
    } catch (err) { toast.error(err.message); }
    e.target.value = '';
  };

  // Voice recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        clearInterval(timerRef.current);
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setTranscribing(true);
        try {
          const result = await api.transcribeAudio(blob);
          if (result.success && result.text) {
            setText(result.text);
            toast.success('Transcribed');
          } else {
            toast.error('Could not detect speech');
          }
        } catch (err) {
          toast.error('Transcription failed');
        } finally {
          setTranscribing(false);
        }
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setRecording(true);
      setRecordingTime(0);
      timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000);
    } catch {
      toast.error('Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setRecording(false);
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.ondataavailable = null;
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
    }
    clearInterval(timerRef.current);
    setRecording(false);
    setRecordingTime(0);
  };

  const formatTime = (s) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`;

  const s = {
    container: {
      padding: '12px 16px 16px',
      borderTop: '1px solid var(--color-border)',
      background: 'var(--color-bg-surface)',
    },
    inner: {
      maxWidth: 'var(--composer-max-width)',
      margin: '0 auto',
    },
    inputArea: {
      display: 'flex',
      alignItems: 'flex-end',
      gap: '8px',
      padding: '10px 14px',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--color-border)',
      background: 'var(--color-bg-elevated)',
      transition: 'border-color 0.15s',
    },
    textarea: {
      flex: 1,
      border: 'none',
      outline: 'none',
      background: 'transparent',
      color: 'var(--color-text-primary)',
      fontSize: '0.9rem',
      lineHeight: 1.5,
      resize: 'none',
      fontFamily: 'inherit',
      maxHeight: '200px',
    },
    iconBtn: (active = false) => ({
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: 32,
      height: 32,
      borderRadius: 'var(--radius-md)',
      border: 'none',
      cursor: 'pointer',
      flexShrink: 0,
      transition: 'all 0.15s',
      background: active ? 'var(--color-accent)' : 'transparent',
      color: active ? 'white' : 'var(--color-text-tertiary)',
    }),
    recordingBar: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      padding: '10px 14px',
      borderRadius: 'var(--radius-lg)',
      background: 'var(--color-error-bg)',
      border: '1px solid var(--color-error)',
    },
    recordDot: {
      width: 10, height: 10, borderRadius: '50%',
      background: 'var(--color-error)',
      animation: 'pulse-dot 1.5s ease-in-out infinite',
    },
  };

  return (
    <div style={s.container}>
      <div style={s.inner}>
        {recording ? (
          <div style={s.recordingBar}>
            <div style={s.recordDot} />
            <span style={{ flex: 1, fontSize: '0.875rem', color: 'var(--color-error)', fontWeight: 500 }}>
              Recording… {formatTime(recordingTime)}
            </span>
            <button style={s.iconBtn()} onClick={cancelRecording} title="Cancel">
              <X size={18} />
            </button>
            <button
              style={{ ...s.iconBtn(true), background: 'var(--color-error)' }}
              onClick={stopRecording}
              title="Stop & transcribe"
            >
              <MicOff size={16} />
            </button>
          </div>
        ) : (
          <div
            style={s.inputArea}
            onFocus={e => { e.currentTarget.style.borderColor = 'var(--color-accent)'; }}
            onBlur={e => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.png,.jpg,.jpeg"
              style={{ display: 'none' }}
              onChange={handleFileAttach}
            />
            <button
              style={s.iconBtn()}
              onClick={() => fileInputRef.current?.click()}
              title="Attach document"
              onMouseEnter={e => { e.target.style.color = 'var(--color-text-primary)'; }}
              onMouseLeave={e => { e.target.style.color = 'var(--color-text-tertiary)'; }}
            >
              <Paperclip size={17} />
            </button>

            <textarea
              ref={textareaRef}
              value={text}
              onChange={e => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={activeDocument ? 'Ask anything about your document…' : 'Upload a document first, or ask a general question…'}
              rows={1}
              style={s.textarea}
              disabled={isLoading || transcribing}
            />

            {transcribing ? (
              <Loader2 size={18} style={{ animation: 'spin 1s linear infinite', color: 'var(--color-accent)', flexShrink: 0 }} />
            ) : (
              <button
                style={s.iconBtn()}
                onClick={startRecording}
                title="Voice input"
                onMouseEnter={e => { e.target.style.color = 'var(--color-text-primary)'; }}
                onMouseLeave={e => { e.target.style.color = 'var(--color-text-tertiary)'; }}
              >
                <Mic size={17} />
              </button>
            )}

            <button
              style={s.iconBtn(!!text.trim() && !isLoading)}
              onClick={handleSend}
              disabled={!text.trim() || isLoading}
              title="Send"
            >
              {isLoading ? (
                <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
              ) : (
                <Send size={16} />
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
