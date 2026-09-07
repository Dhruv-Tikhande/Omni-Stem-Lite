import os
import json
import time
import datetime
import requests

CHATS_DIR = "backend/chats"

# Read Colab URL from env — same source of truth as main.py
COLAB_API_URL = os.getenv(
    "COLAB_API_URL",
    "https://both-seventeen-laboring.ngrok-free.dev"
).rstrip("/")

# ─────────────────────────────────────────────────────────────────────────────
# Diagram Type Classification
# ─────────────────────────────────────────────────────────────────────────────
CHART_TYPES     = {"bar_chart", "line_chart", "line_graph", "pie_chart",
                   "histogram", "scatter_plot", "scatter_chart", "graph"}
SCHEMATIC_TYPES = {"circuit_diagram", "circuit", "flowchart", "schematic",
                   "network_diagram", "block_diagram", "state_diagram"}
TABLE_TYPES     = {"table", "data_table"}
BIO_TYPES       = {"biological_diagram", "anatomy", "cell_diagram", "ecosystem"}
GEO_TYPES       = {"geometric_figure", "geometry", "shape_diagram"}


def _classify(d_type: str) -> str:
    d = d_type.lower().strip()
    if d in CHART_TYPES:     return "chart"
    if d in SCHEMATIC_TYPES: return "schematic"
    if d in TABLE_TYPES:     return "table"
    if d in BIO_TYPES:       return "biological"
    if d in GEO_TYPES:       return "geometric"
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
    lines = []
    lines.append(f"\n  Diagram {idx} ({loc}) — Type: {meta.get('diagram_type', 'Chart')}")
    lines.append(f"    Title   : {meta.get('title', 'Untitled')}")
    lines.append(f"    X-Axis  : {meta.get('x_axis_label', 'Not specified')}")
    lines.append(f"    Y-Axis  : {meta.get('y_axis_label', 'Not specified')}")

    data_points = meta.get("data_points", [])
    if data_points:
        lines.append("    Data Points:")
        for dp in data_points:
            if isinstance(dp, dict):
                lines.append(f"      • {dp.get('label','?')}: {dp.get('value','?')}")
            else:
                lines.append(f"      • {dp}")
    else:
        lines.append("    Data Points: None extracted.")

    if meta.get("key_insight"):
        lines.append(f"    Key Insight : {meta['key_insight']}")
    return lines


def _format_table_diagram(meta: dict, idx: int, loc: str) -> list:
    lines = []
    lines.append(f"\n  Diagram {idx} ({loc}) — Type: {meta.get('diagram_type', 'Table')}")
    lines.append(f"    Title  : {meta.get('title', 'Untitled')}")
    headers = meta.get("headers", [])
    rows    = meta.get("rows", [])
    if headers:
        lines.append(f"    Columns: {', '.join(str(h) for h in headers)}")
    if rows:
        lines.append(f"    Rows ({len(rows)} total):")
        for row in rows[:10]:
            lines.append(f"      • {' | '.join(str(v) for v in row)}")
        if len(rows) > 10:
            lines.append(f"      ... and {len(rows)-10} more rows.")
    if meta.get("key_insight"):
        lines.append(f"    Key Insight: {meta['key_insight']}")
    return lines


def _format_structural_diagram(meta: dict, idx: int, loc: str) -> list:
    lines = []
    comp_strs, rel_strs = [], []
    for c in meta.get("components", []):
        if isinstance(c, dict):
            comp_strs.append(
                f"{c.get('label', c.get('id','?'))} [{c.get('type','?')}] at {c.get('position','?')}"
            )
        else:
            comp_strs.append(str(c))
    for r in meta.get("relationships", []):
        if isinstance(r, dict):
            rel_strs.append(
                f"{r.get('from','?')} → {r.get('to','?')} ({r.get('relationship','?')})"
            )
        else:
            rel_strs.append(str(r))

    lines.append(f"\n  Diagram {idx} ({loc}) — Type: {meta.get('diagram_type','Diagram')}")
    lines.append(f"    Components   : {', '.join(comp_strs) if comp_strs else 'None'}")
    lines.append(f"    Relationships: {'; '.join(rel_strs) if rel_strs else 'None'}")
    return lines


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

        diagrams = doc_data.get("diagrams", [])
        if diagrams:
            lines.append(f"\n[Extracted Diagrams — {len(diagrams)} total]")
            for idx, diag in enumerate(diagrams, 1):
                loc  = diag.get("page_or_index", f"Diagram {idx}")
                meta = diag.get("json_metadata", {})
                if meta.get("error"):
                    lines.append(f"  Diagram {idx} ({loc}): [Processing failed: {meta['error']}]")
                    continue
                category = _classify(meta.get("diagram_type", ""))
                if category == "chart":
                    lines.extend(_format_chart_diagram(meta, idx, loc))
                elif category == "table":
                    lines.extend(_format_table_diagram(meta, idx, loc))
                else:
                    lines.extend(_format_structural_diagram(meta, idx, loc))
        else:
            lines.append("[Extracted Diagrams] None found.")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Diagram Type Detection
# ─────────────────────────────────────────────────────────────────────────────
def _detect_categories(session_data: dict) -> set:
    categories = set()
    for doc_data in session_data.get("documents", {}).values():
        for diag in doc_data.get("diagrams", []):
            d_type = diag.get("json_metadata", {}).get("diagram_type", "")
            if d_type:
                categories.add(_classify(d_type))
    return categories


# ─────────────────────────────────────────────────────────────────────────────
# Master Prompt Builder — category-specific
# ─────────────────────────────────────────────────────────────────────────────
_INSTRUCTIONS = {
    "chart": """The student is asking about a DATA CHART OR GRAPH.
RULES — follow every one strictly:
1. State the chart title and what both axes represent (including units if given).
2. List EVERY category and its EXACT numeric value. E.g.: "Pencil: 12, Scale: 9, Pen: 7".
3. Identify the MAXIMUM value and which category it belongs to.
4. Identify the MINIMUM value and which category it belongs to.
5. State one meaningful comparison or trend.
6. NEVER mention physical wiring, circuit connections, or component flow.
7. Speak conversationally, as if reading the chart aloud to someone who cannot see it.""",

    "schematic": """The student is asking about a CIRCUIT DIAGRAM, FLOWCHART, or SCHEMATIC.
RULES:
1. Describe the spatial layout of components (top, bottom, left, right, center).
2. Trace key connections or flow paths step-by-step.
3. Explain what each component does in plain language.
4. NEVER reference chart axes, bar values, or data points.""",

    "table": """The student is asking about a DATA TABLE.
RULES:
1. Describe what the table is about and list its column headers.
2. Read out the most relevant rows and their values.
3. Highlight highest and lowest values if applicable.
4. Speak row by row, as if describing it to someone who cannot see it.""",

    "biological": """The student is asking about a BIOLOGICAL DIAGRAM.
RULES:
1. Name and describe each labelled structure and its location.
2. Explain the function of each part in plain language.
3. Describe spatial relationships (e.g., "The nucleus is at the centre of the cell").
4. NEVER reference circuit connections or chart data.""",

    "geometric": """The student is asking about a GEOMETRIC FIGURE.
RULES:
1. Name the shape(s) and describe their properties.
2. Describe any labelled measurements or relationships.
3. Use precise spatial language.
4. NEVER reference circuit components or chart values.""",

    "general": """The student is asking about a diagram or document.
RULES:
1. Answer based ONLY on the document context provided.
2. Speak naturally, like a human tutor.
3. If the context is insufficient, say so honestly.""",
}


def _build_master_prompt(user_query: str, context_block: str, categories: set) -> str:
    for priority in ("chart", "schematic", "table", "biological", "geometric", "general"):
        if priority in categories:
            instructions = _INSTRUCTIONS[priority]
            break
    else:
        instructions = _INSTRUCTIONS["general"]

    return f"""You are an expert STEM Tutor for visually impaired students.

DOCUMENT CONTEXT:
{context_block}

STUDENT QUESTION:
\"{user_query}\"

{instructions}

Do NOT mention "JSON", "context block", "session memory", or any internal system terms.

RESPONSE:"""


# ─────────────────────────────────────────────────────────────────────────────
# Colab HTTP Call
# ─────────────────────────────────────────────────────────────────────────────
def _call_colab_text(master_prompt: str) -> str:
    endpoint = f"{COLAB_API_URL}/chat"
    print(f"  → Calling Colab: {endpoint}")
    resp = requests.post(endpoint, json={"prompt": master_prompt}, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    ai_text = data.get("response") or data.get("text") or ""
    if not ai_text:
        raise ValueError(f"Colab returned empty response: {data}")
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
    context_found = bool(session_data.get("documents"))

    context_block = _build_context_block(session_data)
    categories    = _detect_categories(session_data)
    master_prompt = _build_master_prompt(user_query, context_block, categories)

    print(f"  → Context found: {context_found} | Categories: {categories or {'none'}}")
    print(f"  → Prompt: {len(master_prompt)} chars → Colab...")

    try:
        ai_response = _call_colab_text(master_prompt)
        print("  → Colab OK.")
    except requests.exceptions.Timeout:
        ai_response = (
            "I'm sorry — the remote AI server took too long to respond. "
            "Please try again, or check that the Colab notebook is still running."
        )
    except requests.exceptions.ConnectionError:
        ai_response = (
            "I'm sorry — I can't reach the remote AI server. "
            "Please make sure the Colab notebook is running and the ngrok tunnel is active."
        )
    except Exception as e:
        ai_response = (
            f"I'm sorry — an unexpected error occurred: {e}. "
            "Please verify the Colab notebook is running."
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