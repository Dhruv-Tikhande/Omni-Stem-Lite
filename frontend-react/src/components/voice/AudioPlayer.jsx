import { useRef, useState, useEffect } from 'react';
import { Play, Pause, Volume2 } from 'lucide-react';

export default function AudioPlayer({ src, autoPlay = false }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onEnded = () => { setPlaying(false); setProgress(0); };
    const onTimeUpdate = () => setProgress(audio.currentTime);
    const onLoaded = () => setDuration(audio.duration || 0);

    audio.addEventListener('play', onPlay);
    audio.addEventListener('pause', onPause);
    audio.addEventListener('ended', onEnded);
    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('loadedmetadata', onLoaded);

    if (autoPlay) audio.play().catch(() => {});

    return () => {
      audio.removeEventListener('play', onPlay);
      audio.removeEventListener('pause', onPause);
      audio.removeEventListener('ended', onEnded);
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('loadedmetadata', onLoaded);
    };
  }, [src, autoPlay]);

  const toggle = () => {
    const audio = audioRef.current;
    if (!audio) return;
    playing ? audio.pause() : audio.play().catch(() => {});
  };

  const formatTime = (t) => {
    if (!t || isNaN(t)) return '0:00';
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const pct = duration > 0 ? (progress / duration) * 100 : 0;

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '8px',
      padding: '8px 12px', marginTop: '8px',
      borderRadius: 'var(--radius-md)',
      background: 'var(--color-bg-elevated)',
      maxWidth: '320px',
    }}>
      <audio ref={audioRef} src={src} preload="metadata" />

      <button
        onClick={toggle}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          width: 28, height: 28, borderRadius: '50%',
          background: 'var(--color-accent)', color: 'white',
          border: 'none', cursor: 'pointer', flexShrink: 0,
        }}
      >
        {playing ? <Pause size={13} /> : <Play size={13} style={{ marginLeft: '1px' }} />}
      </button>

      <div style={{ flex: 1, height: 4, borderRadius: 2, background: 'var(--color-border)', position: 'relative', cursor: 'pointer' }}
        onClick={e => {
          const rect = e.currentTarget.getBoundingClientRect();
          const pct = (e.clientX - rect.left) / rect.width;
          if (audioRef.current) audioRef.current.currentTime = pct * duration;
        }}
      >
        <div style={{
          height: '100%', borderRadius: 2,
          background: 'var(--color-accent)',
          width: `${pct}%`, transition: 'width 0.1s linear',
        }} />
      </div>

      <span style={{ fontSize: '0.6875rem', color: 'var(--color-text-tertiary)', fontVariantNumeric: 'tabular-nums', minWidth: '32px' }}>
        {formatTime(progress)}
      </span>
    </div>
  );
}
