from dotenv import load_dotenv
load_dotenv()  # loads .env from project root before anything reads os.environ

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import shutil
import os
import io
import json

# Import engines (handles both root and backend/ run contexts)
try:
    from fast_model_engine import analyze_diagram_remote
    from ingestion_engine import ingest_document
    from reasoning_engine import generate_accessible_response
except ImportError:
    from backend.fast_model_engine import analyze_diagram_remote
    from backend.ingestion_engine import ingest_document
    from backend.reasoning_engine import generate_accessible_response

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
COLAB_API_URL = os.getenv(
    "COLAB_API_URL",
    "https://both-seventeen-laboring.ngrok-free.dev"
).rstrip("/")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHATS_DIR = os.path.join(BASE_DIR, "chats")
TEMP_UPLOADS_DIR = os.path.join(BASE_DIR, "..", "temp_uploads")
os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)
os.makedirs(CHATS_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# App Init
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Omni-STEM API", description="AI Backend for Accessibility Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str = "default"
    user_query: str

class RenameRequest(BaseModel):
    title: str


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def health_check():
    return {
        "status": "Omni-STEM Backend is actively running 🚀",
        "colab_url": COLAB_API_URL
    }


# ─────────────────────────────────────────────────────────────────────────────
# Session Management Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/sessions")
def list_sessions():
    """Return a list of all saved sessions with their IDs and titles."""
    sessions = []
    if not os.path.isdir(CHATS_DIR):
        return {"sessions": []}

    for filename in sorted(os.listdir(CHATS_DIR), reverse=True):
        if not filename.endswith(".json"):
            continue
        session_id = filename[:-5]  # strip .json
        path = os.path.join(CHATS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            title = data.get("title", session_id)
            msg_count = len(data.get("messages", []))
            created_at = data.get("created_at")
            sessions.append({
                "session_id": session_id,
                "title": title,
                "message_count": msg_count,
                "created_at": created_at
            })
        except Exception:
            sessions.append({
                "session_id": session_id,
                "title": session_id,
                "message_count": 0,
                "created_at": None
            })

    return {"sessions": sessions}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    """Return the full chat history and document summary for a session."""
    path = os.path.join(CHATS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Return messages + title; strip heavy text_content to keep response small
    doc_summary = {}
    for doc_name, doc_data in data.get("documents", {}).items():
        doc_summary[doc_name] = {
            "diagram_count": len(doc_data.get("visual_hashes", [])),
            "has_text": bool((doc_data.get("text_content") or "").strip())
        }

    return {
        "session_id":    session_id,
        "title":         data.get("title", session_id),
        "messages":      data.get("messages", []),
        "doc_summary":   doc_summary
    }


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session file permanently."""
    path = os.path.join(CHATS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    os.remove(path)
    return {"status": "deleted", "session_id": session_id}


@app.patch("/api/sessions/{session_id}/rename")
def rename_session(session_id: str, req: RenameRequest):
    """Rename a conversation."""
    path = os.path.join(CHATS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    with open(path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["title"] = req.title
        f.seek(0)
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.truncate()
    return {"status": "renamed", "session_id": session_id, "title": req.title}


# ─────────────────────────────────────────────────────────────────────────────
# Transcription Endpoint (Whisper)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from faster_whisper import WhisperModel
    _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    _whisper_available = True
    print("✅ Whisper model loaded for /api/transcribe")
except Exception as e:
    _whisper_model = None
    _whisper_available = False
    print(f"⚠️ Whisper not available: {e}")


@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Accept an audio file, run Whisper, return transcribed text."""
    if not _whisper_available:
        raise HTTPException(status_code=503, detail="Whisper model not available.")

    temp_path = f"temp_uploads/audio_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        segments, info = _whisper_model.transcribe(temp_path, beam_size=5)
        text = " ".join(seg.text for seg in segments).strip()
        os.remove(temp_path)
        return {
            "success": True,
            "text": text,
            "language": info.language,
            "confidence": round(info.language_probability, 3)
        }
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# TTS Endpoint (gTTS)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from gtts import gTTS
    _tts_available = True
except ImportError:
    _tts_available = False


@app.post("/api/tts")
async def text_to_speech(text: str = Form(...)):
    """Convert text to speech audio (MP3). Returns audio/mpeg stream."""
    if not _tts_available:
        raise HTTPException(status_code=503, detail="gTTS not available.")
    try:
        tts = gTTS(text=text, lang="en", tld="co.in")
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Ingestion Endpoint
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/ingest")
async def ingest_document_api(
    file: UploadFile = File(...),
    session_id: str = Form("default")
):
    print(f"📥 Ingestion: '{file.filename}' → session '{session_id}'")

    if not COLAB_API_URL:
        raise HTTPException(status_code=500, detail="COLAB_API_URL is missing.")

    temp_path = os.path.join(TEMP_UPLOADS_DIR, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        telemetry = ingest_document(temp_path, COLAB_API_URL, session_id)
        os.remove(temp_path)
        return {
            "status": "success",
            "session_id": session_id,
            "telemetry": telemetry
        }
    except Exception as e:
        print(f"❌ Ingestion error: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Chat Endpoint
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Conversational endpoint. Reads session memory, calls Colab, persists the turn.
    Does NOT require re-uploading any image.
    """
    print(f"💬 Chat — session: '{request.session_id}' | query: '{request.user_query}'")

    try:
        result = generate_accessible_response(
            session_id=request.session_id,
            user_query=request.user_query
        )
        return {
            "status":          "success",
            "session_id":      request.session_id,
            "response":        result["response"],
            "context_found":   result["context_found"],
            "latency_seconds": result["latency_seconds"]
        }
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return {"status": "error", "response": str(e), "context_found": False}


# ─────────────────────────────────────────────────────────────────────────────
# Legacy Direct Analyze (kept for backward compatibility)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/analyze")
async def analyze_diagram(
    image: UploadFile = File(...),
    query: str = Form(...)
):
    print(f"📥 Analyze: '{query}' | image: '{image.filename}'")
    if not COLAB_API_URL:
        raise HTTPException(status_code=500, detail="COLAB_API_URL is missing.")

    temp_path = f"temp_uploads/{image.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    try:
        ai_response_dict, latency = analyze_diagram_remote(temp_path, query, COLAB_API_URL)
        os.remove(temp_path)
        return {
            "success":         True,
            "query":           query,
            "ai_response":     ai_response_dict,
            "latency_seconds": round(latency, 2)
        }
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"success": False, "error": str(e)}