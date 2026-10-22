# Omni-STEM Lite 🔬

> **An AI-powered STEM accessibility assistant for visually impaired students.**
> Upload documents, diagrams, or images — ask questions in text or voice — and get spoken-language explanations grounded in your material.

---

## Overview

Omni-STEM Lite is a full-stack AI application that bridges the gap between complex STEM materials (circuit diagrams, biology charts, physics graphs, math equations) and students who cannot see them. It uses a **two-stage AI pipeline** — a vision extraction engine followed by a reasoning/explanation engine — to produce accurate, hallucination-resistant, pedagogically useful responses.

The system is built around a **React + Vite** frontend and a **FastAPI** backend, with GroqCloud powering vision analysis.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│   Sidebar (sessions, upload) │ Chat Workspace │ Voice I/O       │
└─────────────────────┬───────────────────────────────────────────┘
                      │  HTTP (FastAPI on :8000)
┌─────────────────────▼───────────────────────────────────────────┐
│                       FastAPI Backend                           │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐   ┌─────────────┐  │
│  │ Ingestion Engine │   │ Reasoning Engine │   │ Voice Layer │  │
│  │ (PDF/DOCX/Image) │   │ (GroqCloud LLM)  │   │ Whisper+TTS │  │
│  └──────────────────┘   └──────────────────┘   └─────────────┘  │
│           │                      │                              │
│  ┌──────────────────┐   ┌──────────────────┐                    │
│  │ Fast Model Engine│   │  Session Store   │                    │
│  │  (Vision / Groq) │   │  (JSON on disk)  │                    │
│  └──────────────────┘   └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

### 📄 Document Ingestion
- Accepts **PDF**, **DOCX**, **PNG**, **JPG/JPEG** uploads
- Extracts embedded images from PDF/DOCX pages via **PyMuPDF**
- MD5-based deduplication caches already-processed visuals (skips re-analysis)
- Stores extracted text + visual metadata in a per-session JSON file

### 🧠 Two-Stage AI Pipeline
1. **Vision Extraction** (`fast_model_engine.py`) — calls GroqCloud's vision model to produce a structured JSON description of each diagram/image. The JSON faithfully captures text, labels, numbers, units, connections, spatial relationships, and uncertainties — no hallucination allowed.
2. **Reasoning Engine** (`reasoning_engine.py`) — a second GroqCloud call that reads the JSON (not the image) and answers the student's question with spoken-language explanations, worked examples, and STEM concept teaching.

### 💬 Session Management
- Multi-session chat history stored as JSON files in `backend/chats/`
- Sessions grouped by date (Today / Yesterday / Previous 7 Days / Older)
- Create, rename, delete, and switch sessions from the sidebar
- Full conversation history persists between page reloads

### 🎤 Voice I/O
- **Voice recording**: Click the mic button to record, stop to transcribe
- **Push-to-Talk**: Hold `Spacebar` to record voice input inline
- **Transcription**: `faster-whisper` (tiny model, `int8` quantized, CPU) converts audio to text
- **Text-to-Speech**: `gTTS` streams MP3 audio of AI responses back to the browser

### ♿ Accessibility & Audio Feedback
- **Screen Reader Announcements**: Live assertive ARIA regions (`AccessibilityContext`) announce recording status, incoming responses, and document uploads
- **Auditory Feedback (Earcons)**: Synthesized sound cues (`audioCues.js` via Web Audio API) signal recording start/stop, processing states, and errors without relying on visual feedback
- **Audio Playback**: Inline audio player (`AudioPlayer`) for streaming and replaying spoken explanations

### 🎨 Rich Frontend UI
- **React 19** with **Vite 8** build tooling
- **TailwindCSS v4** for styling
- **KaTeX** for LaTeX math rendering inside chat messages
- **react-markdown** + **remark-gfm** for full Markdown support in responses
- **react-syntax-highlighter** for code blocks
- **Radix UI** dialogs and tooltips
- **Sonner** toast notifications
- Collapsible sidebar with light / dark / system theme toggle

---

## Project Structure

```
Omni-Stem-Lite/
├── backend/
│   ├── main.py                     # FastAPI app — API routing, endpoints, & CORS
│   ├── fast_model_engine.py        # Vision extraction via GroqCloud (diagram JSON)
│   ├── reasoning_engine.py         # Reasoning & explanation engine via GroqCloud LLM
│   ├── ingestion_engine.py         # PDF/DOCX/image parsing, image extraction & cache
│   ├── image_processor.py          # Image preprocessing, format conversion, & base64
│   ├── pdf_processor.py            # PDF rendering & page-level text extraction
│   ├── voice_engine.py             # Audio transcription (Whisper) & TTS helpers
│   ├── memory_engine.py            # (Legacy) FAISS vector memory & embeddings
│   ├── chats/                      # Session JSON storage (auto-created)
│   ├── layout_cache/               # Diagram analysis JSON cache (auto-created)
│   ├── processed_images/           # Extracted diagram images cache (auto-created)
│   ├── temp_assets/                # Sample test images & diagrams
│   └── setup.bat                   # Windows development setup helper
├── frontend-react/
│   ├── public/                     # Static web assets (favicons, icons)
│   ├── src/
│   │   ├── assets/                 # UI graphics, logos, & illustrations
│   │   ├── components/
│   │   │   ├── chat/               # Chat UI components
│   │   │   │   ├── AssistantMessage.jsx   # AI message bubble with TTS audio player
│   │   │   │   ├── ChatComposer.jsx       # Input bar, mic button, & file upload
│   │   │   │   ├── ChatHeader.jsx         # Header bar with session title & actions
│   │   │   │   ├── ChatWorkspace.jsx      # Main scrollable conversation view
│   │   │   │   ├── MarkdownRenderer.jsx   # Markdown, LaTeX math, & code highlighting
│   │   │   │   ├── MessageList.jsx        # Message history container
│   │   │   │   ├── TypingIndicator.jsx    # Loading / thinking state indicator
│   │   │   │   ├── UserMessage.jsx        # Student message bubble
│   │   │   │   └── WelcomeScreen.jsx      # Empty state with feature highlights
│   │   │   ├── layout/             # Application layout components
│   │   │   │   ├── AppShell.jsx           # Master responsive container
│   │   │   │   └── Sidebar.jsx            # Session history, document status, theme toggle
│   │   │   └── voice/              # Audio playback components
│   │   │       └── AudioPlayer.jsx        # Audio controller for TTS responses
│   │   ├── contexts/               # React Context providers
│   │   │   ├── AccessibilityContext.jsx   # Live ARIA region for screen reader updates
│   │   │   ├── ChatContext.jsx            # Active session state & messaging logic
│   │   │   └── ThemeContext.jsx           # Dark / Light / System theme provider
│   │   ├── hooks/                  # Custom React hooks
│   │   │   └── usePushToTalk.js           # Push-to-Talk keyboard listener (Spacebar)
│   │   ├── services/
│   │   │   └── api.js                     # REST API client for backend communication
│   │   ├── utils/
│   │   │   └── audioCues.js               # Web Audio API sound feedback (mic, status)
│   │   ├── App.jsx                 # Top-level React component tree
│   │   ├── index.css               # TailwindCSS v4 and global theme styling
│   │   └── main.jsx                # Application bootstrap entry point
│   ├── index.html                  # HTML entry point
│   ├── package.json                # Frontend dependencies & npm scripts
│   ├── vite.config.js              # Vite configuration & dev server proxy
│   └── .oxlintrc.json              # Oxlint linter configuration
├── create_test_pdf.py              # Helper to generate synthetic test PDFs with diagrams
├── test_ingestion.py               # Ingestion pipeline validation script
├── requirements.txt                # Python backend dependencies
├── .env.example                    # Environment variable configuration template
└── temp_uploads/                   # Transient document upload staging (auto-created)
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/sessions` | List all chat sessions |
| `GET` | `/api/sessions/{id}` | Get session history + doc summary |
| `DELETE` | `/api/sessions/{id}` | Delete a session |
| `PATCH` | `/api/sessions/{id}/rename` | Rename a session |
| `POST` | `/api/ingest` | Upload & ingest a document into a session |
| `POST` | `/api/chat` | Send a message, get an AI response |
| `POST` | `/api/transcribe` | Transcribe audio to text (Whisper) |
| `POST` | `/api/tts` | Convert text to MP3 audio (gTTS) |
| `POST` | `/api/analyze` | (Legacy) Direct image analysis |

---

## Setup & Running

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [GroqCloud API key](https://console.groq.com/keys)

### 1. Clone & configure environment

```bash
git clone <repo-url>
cd Omni-Stem-Lite

# Copy and fill in your API key
cp .env.example .env
# Edit .env:  GROQ_API_KEY=your_key_here
```

### 2. Backend

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn backend.main:app --reload --port 8000
```

> The backend auto-creates `backend/chats/`, `backend/layout_cache/`, and `temp_uploads/` on first run.

### 3. Frontend

```bash
cd frontend-react
npm install
npm run dev
# Open http://localhost:5173
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | **Yes** | GroqCloud API key for vision & reasoning |
| `COLAB_API_URL` | No (legacy) | Formerly used for a Colab GPU bridge; no longer needed |

---

## Tech Stack

### Backend
| Package | Purpose |
|---------|---------|
| FastAPI + Uvicorn | REST API server |
| PyMuPDF (fitz) | PDF text & image extraction |
| python-docx | DOCX text & image extraction |
| Pillow | Image pre-processing |
| groq >= 0.9.0 | GroqCloud SDK (vision + LLM) |
| faster-whisper | Local speech-to-text (Whisper tiny, int8) |
| gTTS | Google Text-to-Speech |
| faiss-cpu | Vector store (legacy memory engine) |
| sentence-transformers | Embeddings (legacy memory engine) |
| python-dotenv | .env loading |

### Frontend
| Package | Purpose |
|---------|---------|
| React 19 + Vite 8 | UI framework + build |
| TailwindCSS v4 | Styling |
| KaTeX + rehype-katex | Math rendering |
| react-markdown + remark-gfm | Markdown chat messages |
| react-syntax-highlighter | Code block highlighting |
| Radix UI | Accessible dialog & tooltip primitives |
| lucide-react | Icon set |
| Sonner | Toast notifications |
| uuid | Session ID generation |

---

## How It Works — End to End

```
User uploads PDF
      │
      ▼
ingestion_engine.py
  ├─ Extracts full text (PyMuPDF / python-docx)
  ├─ Extracts embedded images
  └─ For each image:
       ├─ Compute MD5 hash
       ├─ If hash cached → skip (cache hit)
       └─ If new → call fast_model_engine.py
                    └─ GroqCloud Vision API
                         → Structured JSON description
                              (stored in layout_cache/)

User asks a question
      │
      ▼
reasoning_engine.py
  ├─ Loads session JSON (text + visual JSON cache)
  ├─ Builds context prompt with text + diagram descriptions
  └─ Calls GroqCloud LLM
       → Spoken-language explanation + worked examples
            → Returned to frontend
```

---

## Known Limitations / Notes

- **No real-time streaming**: Chat responses are returned as a single payload after the LLM finishes.
- **Single document per session**: Uploading a new document overwrites the previous one's context in the session.
- **Whisper runs on CPU**: Transcription may be slow on machines without GPU; the `tiny` model is used to minimize latency.
- **FAISS memory engine** (`memory_engine.py`) is a legacy module and is not actively used in the current chat pipeline.
- **`COLAB_API_URL`** is present in the codebase for backward compatibility but is no longer functionally required.

---

## License

This project is for educational / research use. See individual dependency licenses for third-party packages.
