// frontend-react/src/utils/audioCues.js

let audioCtx = null;

const initAudioContext = () => {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      audioCtx = new AudioContext();
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
};

export const playMicStart = () => {
  const ctx = initAudioContext();
  if (!ctx) return;

  const osc = ctx.createOscillator();
  const gainNode = ctx.createGain();

  osc.type = 'sine';
  osc.frequency.setValueAtTime(440, ctx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(660, ctx.currentTime + 0.08);

  gainNode.gain.setValueAtTime(0.0001, ctx.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + 0.02);
  gainNode.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.08);

  osc.connect(gainNode);
  gainNode.connect(ctx.destination);

  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + 0.08);

  osc.onended = () => {
    osc.disconnect();
    gainNode.disconnect();
  };
};

export const playProcessing = () => {
  const ctx = initAudioContext();
  if (!ctx) return;

  const osc = ctx.createOscillator();
  const gainNode = ctx.createGain();

  osc.type = 'sine';
  osc.frequency.setValueAtTime(520, ctx.currentTime);
  osc.frequency.setValueAtTime(780, ctx.currentTime + 0.1);

  gainNode.gain.setValueAtTime(0.0001, ctx.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.15, ctx.currentTime + 0.05);
  gainNode.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.1);
  
  // Rhythmic second stage
  gainNode.gain.setValueAtTime(0.0001, ctx.currentTime + 0.1);
  gainNode.gain.exponentialRampToValueAtTime(0.15, ctx.currentTime + 0.15);
  gainNode.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.2);

  osc.connect(gainNode);
  gainNode.connect(ctx.destination);

  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + 0.2);

  osc.onended = () => {
    osc.disconnect();
    gainNode.disconnect();
  };
};

export const playSuccess = () => {
  const ctx = initAudioContext();
  if (!ctx) return;

  const osc = ctx.createOscillator();
  const gainNode = ctx.createGain();

  osc.type = 'sine';
  osc.frequency.setValueAtTime(880, ctx.currentTime);

  gainNode.gain.setValueAtTime(0.0001, ctx.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + 0.02);
  gainNode.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.25);

  osc.connect(gainNode);
  gainNode.connect(ctx.destination);

  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + 0.25);

  osc.onended = () => {
    osc.disconnect();
    gainNode.disconnect();
  };
};

export const playError = () => {
  const ctx = initAudioContext();
  if (!ctx) return;

  const osc = ctx.createOscillator();
  const gainNode = ctx.createGain();

  osc.type = 'triangle';
  osc.frequency.setValueAtTime(180, ctx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(120, ctx.currentTime + 0.2);

  gainNode.gain.setValueAtTime(0.0001, ctx.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + 0.02);
  gainNode.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.2);

  osc.connect(gainNode);
  gainNode.connect(ctx.destination);

  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + 0.2);

  osc.onended = () => {
    osc.disconnect();
    gainNode.disconnect();
  };
};
