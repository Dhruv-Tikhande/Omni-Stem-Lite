import os
import json
import time
import datetime
import fitz  # PyMuPDF
import io
import docx
import hashlib
from PIL import Image

try:
    from fast_model_engine import analyze_diagram_remote
except ImportError:
    from backend.fast_model_engine import analyze_diagram_remote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHATS_DIR  = os.path.join(BASE_DIR, "chats")
ASSETS_DIR = os.path.join(BASE_DIR, "..", "temp_assets")
LAYOUT_CACHE_DIR = os.path.join(BASE_DIR, "layout_cache")

os.makedirs(CHATS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(LAYOUT_CACHE_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Hash Helper
# ─────────────────────────────────────────────────────────────────────────────
def _compute_md5(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

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

def save_to_session(session_id: str, document_name: str, text_content: str, visual_hashes: list) -> None:
    """
    Completely overwrites the document context for this session.
    Preserves any existing chat message history.
    Stores only the extracted text and an array of MD5 image hashes.
    """
    existing = _load_session_file(session_id)

    existing["title"]     = document_name
    existing["documents"] = {
        document_name: {
            "text_content": text_content,
            "visual_hashes": visual_hashes  # Changed from diagrams
        }
    }
    
    if "created_at" not in existing:
        existing["created_at"] = datetime.datetime.utcnow().isoformat()

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
                
            md5_hash = _compute_md5(img_path)
            images.append({
                "page_or_index": f"Page {page_num}", 
                "path": img_path,
                "hash": md5_hash
            })

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
            
        md5_hash = _compute_md5(img_path)
        images.append({
            "page_or_index": f"Index {img_index}", 
            "path": img_path,
            "hash": md5_hash
        })

    return text_content, images

def process_image(file_path: str):
    img_filename = os.path.basename(file_path)
    img_path     = os.path.join(ASSETS_DIR, img_filename)
    Image.open(file_path).save(img_path)
    
    md5_hash = _compute_md5(img_path)
    return "", [{"page_or_index": "Image 1", "path": img_path, "hash": md5_hash}]

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

    visual_hashes = []
    
    # Telemetry tracking
    telemetry = {
        "text_blocks": max(1, len(text_content) // 2000) if text_content else 0,
        "visuals_processed": len(images),
        "cache_hits": 0
    }

    for idx, img_info in enumerate(images):
        img_path = img_info["path"]
        md5_hash = img_info["hash"]
        page_or_index = img_info["page_or_index"]
        
        visual_hashes.append({
            "hash": md5_hash,
            "page_or_index": page_or_index
        })
        
        cache_path = os.path.join(LAYOUT_CACHE_DIR, f"{md5_hash}.json")
        
        if os.path.exists(cache_path):
            print(f"⚡ Cache hit for {md5_hash}")
            telemetry["cache_hits"] += 1
            continue

        print(f"🧠 Processing diagram (Cache Miss): {img_path}")
        try:
            ai_response_dict, _ = analyze_diagram_remote(
                img_path,
                "Extract layout, type, and all data in detail.",
                colab_url
            )
            # Only cache a genuinely successful extraction — never cache an error dict
            if isinstance(ai_response_dict, dict) and ai_response_dict.get("error"):
                print(f"⚠️ Not caching failed result for {img_path}: {ai_response_dict.get('error')[:120]}")
                telemetry.setdefault("failed", 0)
                telemetry["failed"] += 1
            else:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(ai_response_dict, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"⚠️ Failed to process {img_path}: {e}")
            telemetry.setdefault("failed", 0)
            telemetry["failed"] += 1

        # Respect Groq per-minute token limits — wait before next image
        if idx < len(images) - 1:
            print("  ⏳ Waiting 60s before next image to respect Groq rate limits...")
            time.sleep(60)

    save_to_session(session_id, os.path.basename(file_path), text_content, visual_hashes)

    return telemetry
