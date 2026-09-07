// const API_BASE = '';
const API_BASE = 'http://localhost:8000';

async function handleResponse(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || body.error || `Request failed (${res.status})`);
  }
  return res.json();
}

// ── Sessions ─────────────────────────────────────────────────────
export async function fetchSessions() {
  const res = await fetch(`${API_BASE}/api/sessions`);
  const data = await handleResponse(res);
  return data.sessions || [];
}

export async function fetchSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
  return handleResponse(res);
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: 'DELETE' });
  return handleResponse(res);
}

export async function renameSession(sessionId, title) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/rename`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  return handleResponse(res);
}

// ── Ingestion ────────────────────────────────────────────────────
export async function ingestDocument(file, sessionId) {
  const form = new FormData();
  form.append('file', file);
  form.append('session_id', sessionId);
  const res = await fetch(`${API_BASE}/api/ingest`, { method: 'POST', body: form });
  return handleResponse(res);
}

// ── Chat ─────────────────────────────────────────────────────────
export async function sendChatMessage(sessionId, userQuery) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, user_query: userQuery }),
  });
  return handleResponse(res);
}

// ── Transcription ────────────────────────────────────────────────
export async function transcribeAudio(audioBlob) {
  const form = new FormData();
  form.append('file', audioBlob, 'recording.webm');
  const res = await fetch(`${API_BASE}/api/transcribe`, { method: 'POST', body: form });
  return handleResponse(res);
}

// ── TTS ──────────────────────────────────────────────────────────
export async function textToSpeech(text) {
  const form = new FormData();
  form.append('text', text);
  const res = await fetch(`${API_BASE}/api/tts`, { method: 'POST', body: form });
  if (!res.ok) throw new Error('TTS request failed');
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

// ── Health ────────────────────────────────────────────────────────
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/`);
  return handleResponse(res);
}
