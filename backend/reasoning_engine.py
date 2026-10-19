import os
import json
import time
import datetime
from groq import Groq

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHATS_DIR = os.path.join(BASE_DIR, "chats")
LAYOUT_CACHE_DIR = os.path.join(BASE_DIR, "layout_cache")

GROQ_MODEL = "openai/gpt-oss-20b"
_groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are the Reasoning & Explanation Engine of OMNI STEM, an accessibility
tutor for visually impaired STEM students.

You do NOT have access to the original image. Your only source of truth
about what the image contains is the structured JSON provided to you below,
which was produced by a separate vision-extraction system. The student
cannot see the image either — they rely entirely on what you say.

============================================================
1. GROUNDING RULE
============================================================

Treat the provided JSON as the complete and only record of what is visible
in the image. Do not claim to "see" anything. Do not add details, values,
labels, or connections that are not present in the JSON, even if they would
be typical for that type of diagram.

If a JSON field is null, "unclear", "unreadable", or listed in
"uncertainties", say so plainly to the student rather than guessing or
smoothing over it (e.g. "the diagram doesn't clearly show R2's value" is
better than inventing a plausible-sounding one). A student who cannot see
the image has no way to catch a wrong guess — never let confidence in your
phrasing exceed the confidence the JSON actually supports.

============================================================
2. YOUR JOB VS THE VISION ENGINE'S JOB
============================================================

The vision engine deliberately did NOT solve problems, perform
calculations, or draw conclusions beyond what's directly extractable.
That responsibility is yours. You should:

- Explain what the image shows, in plain spoken language
- Answer the student's specific question using the JSON as evidence
- Perform relevant calculations, reasoning, or worked examples when useful
  for teaching (e.g. compute current from V and R if both are given)
- Draw on general STEM knowledge to explain *concepts* the diagram
  illustrates

When you go beyond what's directly stated in the JSON — explaining a
concept, performing a calculation, or offering an interpretation — make
that distinction natural and clear in your phrasing (e.g. "the diagram
shows R1 at 390 ohms; using Ohm's law, that means..."), so the student can
tell what's from the image versus what you're teaching on top of it.

============================================================
3. ACCESSIBILITY & SPOKEN-LANGUAGE STYLE
============================================================

Your response will be converted to speech (text-to-speech). Write for the
ear, not the eye:

- No markdown, bullet points, headers, or symbols that don't speak naturally
- Never say "as shown", "as you can see", "in the image above" — the
  student cannot see it
- Narrate spatial layout explicitly and naturally when it matters
  ("the resistor is on the left side, connected to..."), don't assume any
  visual context
- Don't read out internal IDs (e.g. "obj_r1") — refer to components the
  way a teacher would ("the resistor labeled R1", "the 390-ohm resistor")
- Prefer short, clear sentences over long nested ones
- Keep responses focused and conversational — give a complete answer to
  what was asked, not an exhaustive dump of every JSON field, and offer to
  go deeper if there's more to explain

============================================================
4. USING CONVERSATION CONTEXT
============================================================

You may receive:
- Structured document/diagram context for the current session
- Recent conversation turns in this session

Use recent turns for immediate follow-ups ("what about R2?" refers to the
component just discussed). If prior conversation conflicts with the
current document context, the current document context always wins — it's
the ground truth for what's being discussed right now.

If a follow-up question can't be answered from the provided context, the
conversation history, or general STEM knowledge, say so honestly rather
than guessing.

============================================================
4A. FIRST EXPLANATION VS. FOLLOW-UP QUESTIONS
============================================================

Determine which situation you're in from the recent conversation history:

FIRST EXPLANATION (no prior turns, or the student is asking about this
image/document for the first time):
- Give a complete orientation before diving into specifics: what kind of
  diagram/content it is, and a brief overview of its main parts, before
  answering the specific question if one was asked.
- If the student just uploaded something with no specific question yet
  (or asked something generic like "what is this?"), walk through its
  structure in a logical order, covering the overall purpose before
  individual component details.
- It's fine for this response to be longer — the student needs enough
  grounding to ask good follow-up questions afterward.

FOLLOW-UP (prior turns exist about this same image/document):
- Assume the student already has the orientation from the first
  explanation. Do NOT re-explain everything or re-list every component
  again.
- Answer only what was asked, using the conversation history to resolve
  references ("it", "that one", "what about R2") to the correct
  component or concept.
- Keep it tight and specific — a follow-up answer should usually be much
  shorter than a first explanation, unless the question itself demands
  depth (e.g. "walk me through the full calculation").

If you're not sure whether something counts as a genuine follow-up (e.g.
the student changed topic or asked about a different part of the image
than before), lean toward a slightly fuller answer rather than assuming
too much shared context.

============================================================
5. LANGUAGE
============================================================

Respond in the same language the student used in their question
(English, Hindi, or Marathi). Keep component labels, numeric values, and
units in their standard form (e.g. "390 ohms", "R1", "9V") even inside a
Hindi or Marathi sentence, since that's how a teacher would naturally
speak them. Match a natural, conversational tone appropriate for a spoken
tutoring session in that language — not a literal word-for-word
translation of an English textbook style.

Respond only with your spoken answer to the student — no labels, no JSON,
no meta-commentary about your process."""

# ─────────────────────────────────────────────────────────────────────────────
# Diagram Type Classification
# ─────────────────────────────────────────────────────────────────────────────
CHART_TYPES     = {"graph", "chart"}
SCHEMATIC_TYPES = {"circuit_diagram", "engineering_diagram", "technical_drawing",
                   "flowchart", "process_diagram", "architecture_diagram"}
TABLE_TYPES     = {"table"}
BIO_TYPES       = {"biology_diagram"}
GEO_TYPES       = {"mathematical_diagram", "equation"}


def _classify(meta: dict) -> str:
    if isinstance(meta.get("graph_data"), dict) and meta["graph_data"].get("present"):
        return "chart"
    if isinstance(meta.get("table_data"), dict) and meta["table_data"].get("present"):
        return "table"
    image_types = set(
        t.lower() for t in meta.get("image_metadata", {}).get("image_type", [])
    )
    if image_types & SCHEMATIC_TYPES:
        return "schematic"
    if image_types & BIO_TYPES:
        return "biological"
    if image_types & GEO_TYPES:
        return "geometric"
    return "general"


# ─────────────────────────────────────────────────────────────────────────────
# Session File Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _session_path(session_id: str) -> str:
    os.makedirs(CHATS_DIR, exist_ok=True)
    return os.path.join(CHATS_DIR, f"{session_id}.json")


def _load_session(session_id: str) -> dict:
    path = _session_path(session_id)
    if not os.path.exists(path):
        return {"title": "New Chat", "documents": {}, "messages": []}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"title": "New Chat", "documents": {}, "messages": []}


def _append_messages(session_id: str, user_query: str, ai_response: str) -> None:
    """Append the user+assistant turn to the session's persistent message history."""
    data = _load_session(session_id)
    data.setdefault("messages", [])
    if "created_at" not in data:
        data["created_at"] = datetime.datetime.utcnow().isoformat()
    data["messages"].append({"role": "user",      "content": user_query})
    data["messages"].append({"role": "assistant", "content": ai_response})
    with open(_session_path(session_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# Context Block Builder — diagram-type aware
# ─────────────────────────────────────────────────────────────────────────────
def _format_chart_diagram(meta: dict, idx: int, loc: str) -> list:
    gd = meta.get("graph_data", {}) or {}
    lines = []
    lines.append(f"\n  Diagram {idx} ({loc}) — Type: {gd.get('graph_type') or 'Chart'}")
    lines.append(f"    Title   : {gd.get('title') or 'Untitled'}")
    lines.append(f"    X-Axis  : {gd.get('x_axis') or 'Not specified'}")
    lines.append(f"    Y-Axis  : {gd.get('y_axis') or 'Not specified'}")

    series = gd.get("series", [])
    if series:
        lines.append("    Series/Categories:")
        for s in series:
            lines.append(f"      • {s}")

    observations = gd.get("observations", [])
    if observations:
        lines.append("    Observations:")
        for o in observations:
            lines.append(f"      • {o}")
    return lines


def _format_table_diagram(meta: dict, idx: int, loc: str) -> list:
    td = meta.get("table_data", {}) or {}
    lines = []
    lines.append(f"\n  Diagram {idx} ({loc}) — Type: Table")
    lines.append(f"    Title  : {td.get('title') or 'Untitled'}")
    headers = td.get("headers", [])
    rows    = td.get("rows", [])
    if headers:
        lines.append(f"    Columns: {', '.join(str(h) for h in headers)}")
    if rows:
        lines.append(f"    Rows ({len(rows)} total):")
        for row in rows[:10]:
            lines.append(f"      • {' | '.join(str(v) for v in row)}")
        if len(rows) > 10:
            lines.append(f"      ... and {len(rows)-10} more rows.")
    notes = td.get("notes", [])
    for n in notes:
        lines.append(f"    Note: {n}")
    return lines


def _format_structural_diagram(meta: dict, idx: int, loc: str) -> list:
    objs     = meta.get("objects", [])
    rels     = meta.get("relationships", [])
    spatial  = meta.get("spatial_information", [])
    im       = meta.get("image_metadata", {}) or {}

    comp_strs = [
        f"{o.get('label') or o.get('id','?')} [{o.get('type','?')}]"
        + (f": {o.get('description')}" if o.get('description') else "")
        for o in objs
    ]
    rel_strs = [
        f"{r.get('source','?')} → {r.get('target','?')} ({r.get('relationship','?')})"
        for r in rels
    ]
    spatial_strs = [
        f"{s.get('subject','?')} is {s.get('relation','?')} {s.get('reference','?')}"
        for s in spatial
    ]

    lines = []
    diagram_type = ", ".join(im.get("image_type", [])) or "Diagram"
    lines.append(f"\n  Diagram {idx} ({loc}) — Type: {diagram_type}")
    lines.append(f"    Components   : {', '.join(comp_strs) if comp_strs else 'None'}")
    lines.append(f"    Connections  : {'; '.join(rel_strs) if rel_strs else 'None'}")
    lines.append(f"    Spatial Layout: {'; '.join(spatial_strs) if spatial_strs else 'None'}")
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# Semantic Compression
# ─────────────────────────────────────────────────────────────────────────────
def _compress_json_payload(data):
    """Recursively removes None, null, empty lists, and raw coordinate fields."""
    if isinstance(data, dict):
        compressed = {}
        for k, v in data.items():
            if v is None or v == [] or v == "":
                continue
            k_lower = k.lower()
            if k_lower in {"bounding_box", "box", "x", "y", "width", "height", "pixel_coords", "coordinates"}:
                continue
            
            compressed_val = _compress_json_payload(v)
            if compressed_val is not None and compressed_val != [] and compressed_val != {}:
                compressed[k] = compressed_val
        return compressed
    elif isinstance(data, list):
        compressed = []
        for item in data:
            compressed_val = _compress_json_payload(item)
            if compressed_val is not None and compressed_val != [] and compressed_val != {}:
                compressed.append(compressed_val)
        return compressed
    else:
        return data

def _build_context_block(session_data: dict) -> str:
    if not session_data or not session_data.get("documents"):
        return "No prior document context available."

    lines = []
    for doc_name, doc_data in session_data["documents"].items():
        lines.append(f"=== Document: {doc_name} ===")

        text = (doc_data.get("text_content") or "").strip()
        if text:
            lines.append(f"\n[Text Excerpt]\n{text[:3000]}{'...' if len(text) > 3000 else ''}")
        else:
            lines.append("[Text Excerpt] None found.")

        visual_hashes = doc_data.get("visual_hashes", [])
        if visual_hashes:
            lines.append(f"\n[Extracted Diagrams — {len(visual_hashes)} total]")
            for idx, item in enumerate(visual_hashes, 1):
                loc = item.get("page_or_index", f"Diagram {idx}")
                md5_hash = item.get("hash")
                
                if not md5_hash:
                    lines.append(f"  Diagram {idx} ({loc}): [Missing Hash]")
                    continue
                    
                cache_path = os.path.join(LAYOUT_CACHE_DIR, f"{md5_hash}.json")
                if not os.path.exists(cache_path):
                    lines.append(f"  Diagram {idx} ({loc}): [Cache Miss]")
                    continue
                    
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    meta = _compress_json_payload(meta)
                except json.JSONDecodeError:
                    meta = {"error": "Invalid cache JSON"}

                if meta.get("error"):
                    lines.append(f"  Diagram {idx} ({loc}): [Processing failed: {meta['error']}]")
                    continue

                summary = meta.get("summary", {}) or {}
                if summary.get("what_is_shown"):
                    lines.append(f"  Diagram {idx} ({loc}) — Overview: {summary['what_is_shown']}")

                category = _classify(meta)
                if category == "chart":
                    lines.extend(_format_chart_diagram(meta, idx, loc))
                elif category == "table":
                    lines.extend(_format_table_diagram(meta, idx, loc))
                else:
                    lines.extend(_format_structural_diagram(meta, idx, loc))

                uncertainties = meta.get("uncertainties", [])
                if uncertainties:
                    lines.append("    ⚠ Uncertain/unclear elements:")
                    for u in uncertainties:
                        lines.append(f"      • {u.get('target','?')}: {u.get('issue','?')} ({u.get('reason','')})")
        else:
            lines.append("[Extracted Diagrams] None found.")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Diagram Type Detection
# ─────────────────────────────────────────────────────────────────────────────
def _detect_categories(session_data: dict) -> set:
    categories = set()
    for doc_data in session_data.get("documents", {}).values():
        for item in doc_data.get("visual_hashes", []):
            md5_hash = item.get("hash")
            if not md5_hash:
                continue
            
            cache_path = os.path.join(LAYOUT_CACHE_DIR, f"{md5_hash}.json")
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    categories.add(_classify(meta))
                except json.JSONDecodeError:
                    pass
    return categories


# ─────────────────────────────────────────────────────────────────────────────
# Master Prompt Builder
# ─────────────────────────────────────────────────────────────────────────────
def _build_master_prompt(user_query: str, context_block: str, session_history: list) -> list:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    if context_block.strip():
        messages.append({"role": "system", "content": f"DOCUMENT CONTEXT:\n{context_block}"})

    sliced_history = session_history[-12:] if len(session_history) > 12 else session_history
    messages.extend(sliced_history)
    messages.append({"role": "user", "content": user_query})

    return messages


# ─────────────────────────────────────────────────────────────────────────────
# Groq Text Call
# ─────────────────────────────────────────────────────────────────────────────
def _call_groq_text(messages: list) -> str:
    print(f"  → Calling Groq: {GROQ_MODEL}")
    completion = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
    )
    ai_text = completion.choices[0].message.content
    if not ai_text:
        raise ValueError("Groq returned an empty response.")
    return ai_text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def generate_accessible_response(session_id: str, user_query: str) -> dict:
    """
    Main entry point called by /api/chat.
    Returns: {'response', 'context_found', 'latency_seconds'}
    Also persists the conversation turn to the session file.
    """
    start = time.time()
    print(f"\n[ReasoningEngine] Session: {session_id} | Query: {user_query}")

    session_data  = _load_session(session_id)
    session_history = session_data.get("messages", [])
    context_found = bool(session_data.get("documents"))

    context_block = _build_context_block(session_data)
    categories    = _detect_categories(session_data)
    messages_payload = _build_master_prompt(user_query, context_block, session_history)

    print(f"  → Context found: {context_found} | Categories: {categories or {'none'}}")
    print(f"  → Payload: {len(messages_payload)} messages → Groq...")

    try:
        ai_response = _call_groq_text(messages_payload)
        print("  → Groq OK.")
    except Exception as e:
        ai_response = (
            f"I'm sorry — an unexpected error occurred while generating a "
            f"response: {e}. Please try again."
        )

    # Persist conversation turn to session file
    _append_messages(session_id, user_query, ai_response)

    latency = round(time.time() - start, 2)
    print(f"  → Total latency: {latency}s")

    return {
        "response":        ai_response,
        "context_found":   context_found,
        "latency_seconds": latency
    }


# ─────────────────────────────────────────────────────────────────────────────
# Local smoke test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = generate_accessible_response(
        session_id="default",
        user_query="What does this chart show and what are the values?"
    )
    print("\n🤖 AI OUTPUT:")
    print(result["response"])
    print(f"\nContext found: {result['context_found']} | Latency: {result['latency_seconds']}s")