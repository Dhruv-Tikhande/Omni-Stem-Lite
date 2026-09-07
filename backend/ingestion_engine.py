import os
import json
import datetime
import fitz  # PyMuPDF
import io
import docx
from PIL import Image

try:
    from fast_model_engine import analyze_diagram_remote
except ImportError:
    from backend.fast_model_engine import analyze_diagram_remote

CHATS_DIR  = "backend/chats"
ASSETS_DIR = "temp_assets"

os.makedirs(CHATS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session File Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _session_path(session_id: str) -> str:
    return os.path.join(CHATS_DIR, f"{session_id}.json")


def _load_session_file(session_id: str) -> dict:
    path = _session_path(session_id)
    if not os.path.exists(path):
        return {"title": "New Chat", "documents": {}, "messages": []}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"title": "New Chat", "documents": {}, "messages": []}


def _write_session_file(session_id: str, data: dict) -> None:
    path = _session_path(session_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_to_session(session_id: str, document_name: str, text_content: str, diagrams: list) -> None:
    """
    Completely overwrites the document context for this session.
    Preserves any existing chat message history.
    Sets the session title from the document filename.
    """
    existing = _load_session_file(session_id)

    existing["title"]     = document_name          # title = ingested filename
    existing["documents"] = {                       # full overwrite of doc context
        document_name: {
            "text_content": text_content,
            "diagrams":     diagrams
        }
    }
    # Set created_at only on first creation — never overwrite
    if "created_at" not in existing:
        existing["created_at"] = datetime.datetime.utcnow().isoformat()

    # messages are PRESERVED — ingestion doesn't wipe conversation history

    _write_session_file(session_id, existing)


# ─────────────────────────────────────────────────────────────────────────────
# File Parsers
# ─────────────────────────────────────────────────────────────────────────────
def process_pdf(file_path: str):
    doc = fitz.open(file_path)
    text_content = ""
    images = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_content += page.get_text() + "\n"

        for img_index, img_info in enumerate(page.get_images(full=True)):
            xref        = img_info[0]
            base_image  = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext   = base_image["ext"]
            img_filename = f"{os.path.basename(file_path)}_p{page_num}_i{img_index}.{image_ext}"
            img_path     = os.path.join(ASSETS_DIR, img_filename)

            with open(img_path, "wb") as f:
                f.write(image_bytes)
            images.append({"page_or_index": f"Page {page_num}", "path": img_path})

    return text_content, images


def process_docx(file_path: str):
    doc = docx.Document(file_path)
    text_content = "\n".join(para.text for para in doc.paragraphs)
    images = []

    for img_index, rel in enumerate(
        (r for r in doc.part.rels.values() if "image" in r.target_ref)
    ):
        img_filename = f"{os.path.basename(file_path)}_i{img_index}.png"
        img_path     = os.path.join(ASSETS_DIR, img_filename)
        with open(img_path, "wb") as f:
            f.write(rel.target_part.blob)
        images.append({"page_or_index": f"Index {img_index}", "path": img_path})

    return text_content, images


def process_image(file_path: str):
    img_filename = os.path.basename(file_path)
    img_path     = os.path.join(ASSETS_DIR, img_filename)
    Image.open(file_path).save(img_path)
    return "", [{"page_or_index": "Image 1", "path": img_path}]


# ─────────────────────────────────────────────────────────────────────────────
# Main Ingestion Entry Point
# ─────────────────────────────────────────────────────────────────────────────
def ingest_document(file_path: str, colab_url: str, session_id: str = "default") -> dict:
    filename = os.path.basename(file_path).lower()

    if filename.endswith(".pdf"):
        text_content, images = process_pdf(file_path)
    elif filename.endswith(".docx"):
        text_content, images = process_docx(file_path)
    elif filename.endswith((".png", ".jpg", ".jpeg")):
        text_content, images = process_image(file_path)
    else:
        raise ValueError(f"Unsupported file format: {filename}")

    diagrams_json = []
    for img_info in images:
        img_path = img_info["path"]
        print(f"🧠 Processing diagram: {img_path}")
        try:
            ai_response_dict, _ = analyze_diagram_remote(
                img_path,
                "Extract layout, type, and all data in detail.",
                colab_url
            )
            diagrams_json.append({
                "page_or_index": img_info["page_or_index"],
                "json_metadata": ai_response_dict
            })
        except Exception as e:
            print(f"⚠️ Failed to process {img_path}: {e}")
            diagrams_json.append({
                "page_or_index": img_info["page_or_index"],
                "json_metadata": {"error": str(e)}
            })

    save_to_session(session_id, os.path.basename(file_path), text_content, diagrams_json)

    return {
        "text_pages_est":    max(1, len(text_content) // 2000) if text_content else 0,
        "diagrams_extracted": len(diagrams_json)
    }
