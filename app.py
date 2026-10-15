import streamlit as st
import os
import json
import io
import zipfile
import tempfile
from datetime import datetime
from ask import ask
from capture import capture_note, capture_link, capture_file
from classify import process_classification
from link import process_linking
from build_graph import build_graph
import streamlit.components.v1 as components
from lib.storage import read_wiki_notes, load_index, save_index, write_wiki_note, generate_capture_id, write_raw_capture, content_hash
from lib.llm import _get_client, _get_model, classify_content
from lib.models import WikiNote, CaptureMeta

# Page Configuration
st.set_page_config(
    page_title="SecondSelf — Cognitive Cortex",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cybernetic Neural Cockpit CSS (Stitch Design Tokens)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --bg-surface: #10131a;
        --bg-container-low: #191b23;
        --bg-container: #1d1f27;
        --bg-container-high: #272a32;
        --primary: #4cd7f6;
        --primary-glow: rgba(76, 215, 246, 0.2);
        --tertiary: #4edea3;
        --secondary: #c0c1ff;
        --border-color: #233047;
        --text-primary: #e1e2ec;
        --text-muted: #869397;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-surface) !important;
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    [data-testid="stHeader"] {
        background: rgba(16, 19, 26, 0.95) !important;
        border-bottom: 1px solid var(--border-color);
    }

    [data-testid="stSidebar"] {
        background-color: #0b0e15 !important;
        border-right: 1px solid var(--border-color) !important;
    }

    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.02em !important;
        color: #ffffff !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 0px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-weight: 600 !important;
        transition: all 0.15s ease-in-out !important;
        border: 1px solid var(--border-color) !important;
    }

    .stButton > button[kind="primary"] {
        background-color: var(--primary) !important;
        color: #003640 !important;
        border: 1px solid var(--primary) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #acedff !important;
        box-shadow: 0 0 16px var(--primary-glow) !important;
    }

    .stButton > button[kind="secondary"] {
        background-color: var(--bg-container-high) !important;
        color: var(--text-primary) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--primary) !important;
        color: var(--primary) !important;
    }

    /* Input Fields */
    .stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {
        border-radius: 0px !important;
        background-color: #0b0e15 !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 1px var(--primary) !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 1px dashed var(--border-color) !important;
        background-color: #0b0e15 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--bg-container-low);
        padding: 4px;
        border-radius: 0px;
        border: 1px solid var(--border-color);
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: var(--text-muted) !important;
        padding: 8px 16px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--bg-container-high) !important;
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary) !important;
    }

    /* Cards */
    .stitch-card {
        background-color: var(--bg-container-low);
        border: 1px solid var(--border-color);
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .stitch-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }

    /* Citation Badges */
    .citation-badge {
        background-color: rgba(76, 215, 246, 0.12);
        color: var(--primary);
        padding: 2px 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        border: 1px solid rgba(76, 215, 246, 0.3);
        display: inline-block;
        margin: 0 2px;
    }
    .para-badge {
        padding: 2px 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        border-left: 2px solid;
    }
    .para-Projects { background: rgba(78, 222, 163, 0.1); color: #4edea3; border-color: #4edea3; }
    .para-Areas { background: rgba(192, 193, 255, 0.1); color: #c0c1ff; border-color: #c0c1ff; }
    .para-Resources { background: rgba(76, 215, 246, 0.1); color: #4cd7f6; border-color: #4cd7f6; }
    .para-Archives { background: rgba(139, 92, 246, 0.1); color: #a78bfa; border-color: #a78bfa; }

    /* Toggle */
    .toggle-on { background: var(--primary) !important; }

    /* Search panel overlay */
    .search-result-item {
        padding: 0.5rem 0.75rem;
        border: 1px solid var(--border-color);
        margin-bottom: 0.5rem;
        cursor: pointer;
        background: var(--bg-container-low);
    }
    .search-result-item:hover {
        border-color: var(--primary);
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "last_answer" not in st.session_state:
    st.session_state.last_answer = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "deep_research" not in st.session_state:
    st.session_state.deep_research = False
if "search_open" not in st.session_state:
    st.session_state.search_open = False
if "queue_filter" not in st.session_state:
    st.session_state.queue_filter = "all"


# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_stats():
    notes = len(read_wiki_notes())
    nodes = 0
    edges = 0
    graph_path = os.path.join("data", "graph.json")
    if os.path.exists(graph_path):
        try:
            with open(graph_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                nodes = data.get("metadata", {}).get("node_count", 0)
                edges = data.get("metadata", {}).get("edge_count", 0)
        except Exception:
            pass
    return notes, nodes, edges


def save_answer_as_note(query: str, answer: str):
    """Save the LLM answer as a new wiki note in the vault."""
    capture_id = generate_capture_id()
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    body = f"## Query\n{query}\n\n## Synthesized Answer\n{answer}"
    hash_val = content_hash(body)

    meta = CaptureMeta(
        id=capture_id,
        timestamp=timestamp,
        type="note",
        source="ask-panel",
        content_hash=hash_val
    )
    write_raw_capture(meta, body)

    # Immediately classify and write to wiki
    result = classify_content(body)
    category = result.get("para", "Archives")
    if category not in ["Projects", "Areas", "Resources", "Archives"]:
        category = "Archives"

    note = WikiNote(
        id=capture_id.split("_")[-1],
        raw_id=capture_id,
        para=category,
        tags=result.get("tags", []),
        summary=result.get("summary", f"Synthesis: {query[:60]}"),
        created=timestamp,
        links=[],
        body=body
    )
    write_wiki_note(note)
    return note


def export_vault_zip() -> bytes:
    """Export all wiki notes as a zip archive."""
    wiki_dir = "wiki"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(wiki_dir):
            for root, _, files in os.walk(wiki_dir):
                for f in files:
                    full_path = os.path.join(root, f)
                    arcname = os.path.relpath(full_path, start=wiki_dir)
                    zf.write(full_path, arcname)
    buf.seek(0)
    return buf.getvalue()


def export_answer_as_markdown(query: str, answer: str, sources: list) -> str:
    """Export the answer as a formatted Markdown string."""
    sources_md = ""
    if sources:
        sources_md = "\n\n## Sources\n"
        for s in sources:
            sources_md += f"- **[{s['id']}]** {s['summary']} — Match: `{s['relevance_score']*100:.1f}%` ({s.get('para', 'Note')})\n"
    return f"""# SecondSelf Synthesis Export

**Query:** {query}

**Generated at:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

---

## Answer

{answer}
{sources_md}
"""


def ask_deep(question: str, top_k: int = 5) -> object:
    """
    Deep Research Mode: multi-hop retrieval.
    1st pass -> get answer + sources -> extract follow-up concepts -> 2nd pass -> merge + synthesize.
    """
    from lib.embeddings import embed_text, load_embeddings, cosine_similarity
    from lib.llm import synthesize_answer, call_llm
    from lib.models import AskResult

    query_emb = embed_text(question)
    embeddings_dict = load_embeddings()

    if not embeddings_dict:
        return AskResult(answer="No embeddings found. Run the pipeline first.", sources=[])

    scores = sorted(
        [(nid, cosine_similarity(query_emb, emb)) for nid, emb in embeddings_dict.items()],
        key=lambda x: x[1],
        reverse=True
    )
    top_k1 = [s for s in scores[:top_k] if s[1] > 0.15]
    all_notes = {n.id: n for n in read_wiki_notes()}

    sources = []
    pass1_text = ""
    for note_id, score in top_k1:
        if note_id in all_notes:
            note = all_notes[note_id]
            sources.append({"id": note.id, "summary": note.summary, "relevance_score": score, "para": note.para})
            pass1_text += f"--- Note [{note.id}] ---\nSummary: {note.summary}\nContent: {note.body[:1000]}\n\n"

    # 1st synthesis
    pass1_answer = synthesize_answer(context=pass1_text, question=question)

    # Extract key concepts for 2nd hop
    concept_prompt = f"""From this synthesis, extract 3-5 key technical concepts or topics that could benefit from deeper research.
Return ONLY a JSON array of short strings (concept names), e.g. ["concept1", "concept2"].

Synthesis:
{pass1_answer}
"""
    try:
        concepts_raw = call_llm(concept_prompt, system="You output only valid JSON arrays.", response_format="json")
        concepts = json.loads(concepts_raw)
        if not isinstance(concepts, list):
            raise ValueError("Not a list")
    except Exception:
        concepts = [question]

    # 2nd hop
    additional_sources = []
    hop2_text = pass1_text
    seen_ids = {s["id"] for s in sources}

    for concept in concepts[:3]:
        c_emb = embed_text(concept)
        c_scores = sorted(
            [(nid, cosine_similarity(c_emb, emb)) for nid, emb in embeddings_dict.items()],
            key=lambda x: x[1],
            reverse=True
        )
        for nid, score in c_scores[:3]:
            if nid not in seen_ids and score > 0.2 and nid in all_notes:
                note = all_notes[nid]
                additional_sources.append({"id": note.id, "summary": note.summary, "relevance_score": score, "para": note.para})
                hop2_text += f"--- Note [{note.id}] (Deep Hop) ---\nSummary: {note.summary}\nContent: {note.body[:800]}\n\n"
                seen_ids.add(nid)

    # Final synthesis from all gathered context
    final_answer = synthesize_answer(
        context=hop2_text,
        question=f"{question}\n\nAlso synthesize connections to: {', '.join(concepts[:3])}"
    )
    all_sources = sources + additional_sources
    return AskResult(answer=final_answer, sources=all_sources)


def get_raw_captures_info():
    """Return list of raw captures with their status from the index."""
    from lib.storage import read_raw_captures
    index = load_index()
    processed = index.get("raw_processed", {})
    captures = read_raw_captures()
    result = []
    for meta, content in captures:
        status = "completed" if meta.id in processed else "pending"
        result.append({
            "id": meta.id,
            "type": meta.type,
            "source": meta.source,
            "timestamp": meta.timestamp,
            "status": status,
            "preview": content[:200] if content else ""
        })
    return result


notes_count, nodes_count, edges_count = get_stats()

active_model = "Auto-Detect"
try:
    client = _get_client()
    active_model = _get_model(client)
except Exception:
    active_model = "Llama/Groq Fallback"


# ==========================================
# SIDEBAR: CORTEX CONTROLLER & TELEMETRY
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style='display:flex; align-items:center; gap:0.75rem; margin-bottom:1.5rem; padding-bottom:1rem; border-bottom:1px solid #233047;'>
        <div style='font-size:1.8rem;'>🧠</div>
        <div>
            <div style='font-family:"Space Grotesk"; font-size:1.2rem; font-weight:700; color:#ffffff;'>SecondSelf</div>
            <div style='font-size:0.7rem; color:#4cd7f6; letter-spacing:0.1em; text-transform:uppercase;'>Cortex Node v2.5</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Ingestion Center
    st.markdown("<div style='font-size:0.75rem; color:#869397; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;'>Capture Stream</div>", unsafe_allow_html=True)
    capture_fmt = st.selectbox("Type", ["Quick Note", "Web Link", "File Upload"], label_visibility="collapsed")

    if capture_fmt == "Quick Note":
        note_input = st.text_area("Thought", placeholder="Capture a thought, task, or insight...", label_visibility="collapsed", height=90)
        if st.button("Capture Note", use_container_width=True, type="primary"):
            if note_input.strip():
                capture_note(note_input)
                st.success("Captured to brain stream!")
                st.rerun()
            else:
                st.error("Text cannot be empty.")

    elif capture_fmt == "Web Link":
        url_input = st.text_input("URL", placeholder="https://...", label_visibility="collapsed")
        notes_context = st.text_area("Context", placeholder="Optional context...", label_visibility="collapsed", height=65)
        if st.button("Ingest Link", use_container_width=True, type="primary"):
            if url_input.strip():
                capture_link(url_input, notes_context)
                st.success("Web link ingested!")
                st.rerun()
            else:
                st.error("Please enter a valid URL.")

    else:  # File Upload
        uploaded_file = st.file_uploader(
            "Drop file here",
            type=["pdf", "txt", "md", "csv", "mp3", "wav"],
            label_visibility="collapsed",
            help="PDF, TXT, MD, CSV, MP3, WAV — max 50MB"
        )
        if st.button("Ingest File", use_container_width=True, type="primary"):
            if uploaded_file is not None:
                # Save to temp path then capture
                suffix = os.path.splitext(uploaded_file.name)[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                try:
                    capture_file(tmp_path)
                    st.success(f"File '{uploaded_file.name}' ingested!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    os.unlink(tmp_path)
            else:
                st.error("Please select a file to upload.")

    st.markdown("<hr style='border:none; border-top:1px solid #233047; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # Pipeline Controller
    st.markdown("<div style='font-size:0.75rem; color:#869397; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;'>Pipeline Runtime</div>", unsafe_allow_html=True)
    force_proc = st.checkbox("Force full rebuild")
    if st.button("Execute Pipeline", use_container_width=True):
        with st.status("Executing Cognitive Pipeline...", expanded=True) as status:
            if force_proc:
                idx = load_index()
                idx["raw_processed"] = {}
                save_index(idx)
            st.write("1. Classifying notes (PARA)...")
            process_classification()
            st.write("2. Computing vector embeddings & links...")
            process_linking()
            st.write("3. Compiling force-directed graph...")
            build_graph()
            status.update(label="Pipeline execution complete!", state="complete")
        st.rerun()

    st.markdown("<hr style='border:none; border-top:1px solid #233047; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # Vault Export
    st.markdown("<div style='font-size:0.75rem; color:#869397; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;'>Vault Actions</div>", unsafe_allow_html=True)

    if st.button("📦 Export Vault (ZIP)", use_container_width=True):
        with st.spinner("Packing vault..."):
            vault_zip = export_vault_zip()
        fname = f"secondself_vault_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        st.download_button(
            label="⬇ Download Vault ZIP",
            data=vault_zip,
            file_name=fname,
            mime="application/zip",
            use_container_width=True
        )

    st.markdown("<hr style='border:none; border-top:1px solid #233047; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # Telemetry Stats
    st.markdown("<div style='font-size:0.75rem; color:#869397; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.75rem;'>Telemetry Deck</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background:#10131a; border:1px solid #233047; padding:0.75rem; display:flex; flex-direction:column; gap:0.5rem; font-size:0.75rem;'>
        <div style='display:flex; justify-content:space-between;'><span style='color:#869397;'>LLM Engine:</span><span style='color:#4cd7f6;'>{active_model.split('/')[-1]}</span></div>
        <div style='display:flex; justify-content:space-between;'><span style='color:#869397;'>Wiki Notes:</span><span style='color:#ffffff; font-weight:700;'>{notes_count}</span></div>
        <div style='display:flex; justify-content:space-between;'><span style='color:#869397;'>Graph Nodes:</span><span style='color:#4edea3; font-weight:700;'>{nodes_count}</span></div>
        <div style='display:flex; justify-content:space-between;'><span style='color:#869397;'>Semantic Edges:</span><span style='color:#c0c1ff; font-weight:700;'>{edges_count}</span></div>
        <div style='display:flex; justify-content:space-between;'><span style='color:#869397;'>Vector Embedding:</span><span style='color:#4edea3;'>all-MiniLM-L6</span></div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# MAIN INTERFACE
# ==========================================

# Top Header
st.markdown("""
<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem; border-bottom:1px solid #233047; padding-bottom:0.75rem;'>
    <div>
        <h1 style='margin:0; font-size:1.8rem; font-weight:700; color:#ffffff; display:flex; align-items:center; gap:0.5rem;'>
            🧠 SecondSelf <span style='font-size:0.75rem; background:rgba(76,215,246,0.15); color:#4cd7f6; padding:2px 8px; border:1px solid #4cd7f6; font-family:"JetBrains Mono"; font-weight:500;'>ONLINE</span>
        </h1>
        <div style='font-size:0.85rem; color:#869397; margin-top:2px;'>Cybernetic Neural Knowledge Cockpit — Capture, Classify, Link, Synthesize.</div>
    </div>
    <div style='text-align:right;'>
        <span style='font-size:0.75rem; color:#4edea3; background:#191b23; padding:4px 10px; border:1px solid #233047;'>● CHROMA & GROQ ACTIVE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab_ask, tab_graph, tab_para, tab_capture, tab_search = st.tabs([
    "🧠  ASK YOUR BRAIN",
    "🕸️  KNOWLEDGE GRAPH",
    "📁  PARA VAULT",
    "⚡  CAPTURE QUEUE",
    "🔍  SEARCH VAULT"
])


# ==========================================
# TAB 1: ASK YOUR BRAIN (RAG SYNTHESIS)
# ==========================================
with tab_ask:
    # Controls row
    col_mode, col_info = st.columns([3, 1])
    with col_mode:
        st.markdown("""
        <div class='stitch-card'>
            <div class='stitch-card-header'>
                <span style='font-size:0.75rem; text-transform:uppercase; color:#869397;'>RAG Natural Language Synthesis Engine</span>
                <span style='font-size:0.75rem; color:#4edea3;'>Top_K=5 · Temperature 0.10</span>
            </div>
        """, unsafe_allow_html=True)

    with col_info:
        deep_mode = st.toggle("🔬 Deep Research Mode", value=st.session_state.deep_research, key="deep_research_toggle",
                               help="Multi-hop retrieval: performs 2-pass semantic search for richer synthesis")
        st.session_state.deep_research = deep_mode

    col_q, col_btn = st.columns([6, 1])
    with col_q:
        q_val = st.text_input("Query", placeholder="> What are my current tasks and project priorities?", label_visibility="collapsed",
                               value=st.session_state.get("prefill_query", ""))
    with col_btn:
        ask_trigger = st.button("Synthesize", type="primary", use_container_width=True)

    # Quick prompt suggestions
    st.markdown("""
    <div style='display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.25rem; font-size:0.75rem;'>
        <span style='color:#869397;'>Suggestions:</span>
        <span style='color:#4cd7f6; cursor:pointer;'>• when to complete homework</span>
        <span style='color:#4cd7f6; cursor:pointer;'>• what are my career goals</span>
        <span style='color:#4cd7f6; cursor:pointer;'>• project deadlines</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if ask_trigger and q_val.strip():
        st.session_state.last_query = q_val
        mode_label = "Multi-Hop Deep Research" if st.session_state.deep_research else "Standard RAG"
        with st.spinner(f"Executing {mode_label} retrieval & LLM synthesis..."):
            if st.session_state.deep_research:
                res = ask_deep(q_val)
            else:
                res = ask(q_val)
            st.session_state.last_answer = res

    res = st.session_state.last_answer

    if res:
        # Answer Box
        st.markdown(f"""
        <div class='stitch-card' style='border-left: 3px solid #4cd7f6;'>
            <div class='stitch-card-header'>
                <div style='display:flex; align-items:center; gap:0.5rem;'>
                    <span style='color:#4cd7f6;'>⚡</span>
                    <span style='font-weight:700; color:#ffffff;'>Synthesized Cognitive Conclusion</span>
                    {'<span style="font-size:0.7rem; background:rgba(78,222,163,0.15); color:#4edea3; padding:1px 6px; border:1px solid #4edea3; margin-left:0.5rem;">DEEP RESEARCH</span>' if st.session_state.deep_research else ''}
                </div>
                <span style='font-size:0.75rem; color:#4edea3; font-family:"JetBrains Mono";'>Grounded from Vault</span>
            </div>
            <div style='font-size:1.05rem; line-height:1.7; color:#f1f5f9; padding:0.5rem 0;'>
                {res.answer}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action toolbar
        st.markdown("<div style='font-size:0.8rem; color:#869397; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;'>Answer Actions</div>", unsafe_allow_html=True)
        col_copy, col_save, col_export, col_regen = st.columns(4)

        with col_copy:
            # Copy to clipboard using JS
            escaped = res.answer.replace("'", "\\'").replace("\n", "\\n").replace('"', '\\"')
            st.markdown(f"""
            <button onclick="navigator.clipboard.writeText('{escaped}').then(()=>{{this.textContent='✓ Copied!'; setTimeout(()=>this.textContent='📋 Copy Answer',1500)}})" 
                style="width:100%;padding:0.5rem;background:#272a32;border:1px solid #233047;color:#4cd7f6;font-family:'JetBrains Mono';font-size:0.75rem;text-transform:uppercase;cursor:pointer;letter-spacing:0.05em;">
                📋 Copy Answer
            </button>
            """, unsafe_allow_html=True)

        with col_save:
            if st.button("💾 Save as Note", use_container_width=True, key="save_note_btn"):
                with st.spinner("Saving to vault..."):
                    note = save_answer_as_note(st.session_state.last_query, res.answer)
                st.success(f"Saved → wiki/{note.para}/{note.id}.md")

        with col_export:
            md_content = export_answer_as_markdown(
                st.session_state.last_query, res.answer,
                res.sources if res.sources else []
            )
            st.download_button(
                label="⬇ Export MD",
                data=md_content.encode("utf-8"),
                file_name=f"synthesis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
                key="export_md_btn"
            )

        with col_regen:
            if st.button("🔄 Regenerate", use_container_width=True, key="regen_btn"):
                if st.session_state.last_query:
                    with st.spinner("Re-synthesizing..."):
                        if st.session_state.deep_research:
                            st.session_state.last_answer = ask_deep(st.session_state.last_query)
                        else:
                            st.session_state.last_answer = ask(st.session_state.last_query)
                    st.rerun()

        # Sources Section
        if res.sources:
            st.markdown("<div style='font-size:0.85rem; font-weight:700; text-transform:uppercase; color:#869397; margin:1rem 0 0.5rem 0;'>Retrieved Semantic Evidence</div>", unsafe_allow_html=True)
            src_cols = st.columns(min(len(res.sources), 3))
            for idx_s, s in enumerate(res.sources):
                col_target = src_cols[idx_s % len(src_cols)]
                with col_target:
                    para_class = f"para-{s.get('para', 'Archives')}"
                    is_deep = "(Deep Hop)" if idx_s >= 5 else ""
                    st.markdown(f"""
                    <div class='stitch-card' style='height:100%;'>
                        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;'>
                            <span class='citation-badge'>[{s['id']}]</span>
                            <span class='para-badge {para_class}'>{s.get('para', 'Note')}</span>
                        </div>
                        <div style='font-weight:600; color:#ffffff; font-size:0.9rem; margin-bottom:0.5rem;'>{s['summary']}</div>
                        <div style='display:flex; justify-content:space-between; font-size:0.75rem; color:#869397; margin-top:auto;'>
                            <span>Cosine Match {is_deep}</span>
                            <span style='color:#4edea3; font-weight:700;'>{s['relevance_score']*100:.1f}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


# ==========================================
# TAB 2: KNOWLEDGE GRAPH
# ==========================================
with tab_graph:
    col_g_head, col_g_btn = st.columns([5, 1])
    with col_g_head:
        st.markdown("<div style='font-size:0.85rem; color:#869397;'>Interactive 2D force-directed knowledge graph with semantic node clustering.</div>", unsafe_allow_html=True)
    with col_g_btn:
        if st.button("Refresh Graph", use_container_width=True):
            st.rerun()

    graph_path = os.path.join("static", "graph.html")
    if os.path.exists(graph_path):
        with open(graph_path, 'r', encoding='utf-8') as f:
            html_template = f.read()

        json_path = os.path.join("data", "graph.json")
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                graph_json = f.read()
        else:
            graph_json = '{"nodes": [], "edges": [], "metadata": {"node_count": 0, "edge_count": 0}}'

        html_data = html_template.replace("GRAPH_JSON_DATA", graph_json)
        html_data = html_data.replace("<header>", "<header style='display:none;'>")

        st.markdown('<div style="border: 1px solid #233047; overflow: hidden; margin-top:0.75rem;">', unsafe_allow_html=True)
        components.html(html_data, height=650, scrolling=False)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Graph data not compiled yet. Please run the pipeline from the sidebar.")


# ==========================================
# TAB 3: PARA VAULT EXPLORER
# ==========================================
with tab_para:
    all_notes = read_wiki_notes()

    # Vault header with actions
    v_col1, v_col2, v_col3 = st.columns([4, 1, 1])
    with v_col1:
        if not all_notes:
            st.info("No wiki notes found yet in the vault.")
    with v_col2:
        if all_notes:
            # Export vault button
            vault_zip_data = export_vault_zip()
            fname_vault = f"vault_{datetime.now().strftime('%Y%m%d')}.zip"
            st.download_button(
                "📦 Export Vault",
                data=vault_zip_data,
                file_name=fname_vault,
                mime="application/zip",
                use_container_width=True,
                key="export_vault_para"
            )
    with v_col3:
        if all_notes:
            if st.button("🔀 Auto-Rebalance", use_container_width=True, help="Re-classify all unprocessed notes using AI PARA routing", key="rebalance_btn"):
                with st.spinner("Re-classifying all notes with AI..."):
                    # Force full reclassification
                    idx = load_index()
                    idx["raw_processed"] = {}
                    save_index(idx)
                    process_classification()
                st.success("Auto-rebalance complete! All notes re-classified.")
                st.rerun()

    if all_notes:
        para_categories = ["All", "Projects", "Areas", "Resources", "Archives"]
        sel_cat = st.selectbox("Filter Category", para_categories, horizontal=True)

        filtered = [n for n in all_notes if sel_cat == "All" or n.para == sel_cat]
        st.markdown(f"<div style='font-size:0.8rem; color:#869397; margin-bottom:1rem;'>Showing {len(filtered)} of {len(all_notes)} vault artifacts.</div>", unsafe_allow_html=True)

        # Search within PARA
        para_search = st.text_input("🔍 Filter notes", placeholder="Search by title, tag, or content...", label_visibility="collapsed", key="para_filter")
        if para_search:
            filtered = [n for n in filtered if
                        para_search.lower() in n.summary.lower() or
                        para_search.lower() in n.body.lower() or
                        any(para_search.lower() in t.lower() for t in n.tags)]

        grid_cols = st.columns(2)
        for i, n in enumerate(filtered):
            col_target = grid_cols[i % 2]
            with col_target:
                para_class = f"para-{n.para}"
                tags_html = " ".join([f"<span style='background:#10131a; color:#869397; padding:1px 5px; font-size:0.7rem; border:1px solid #233047;'>#{t}</span>" for t in n.tags])
                with st.expander(f"[{n.id}] {n.summary} ({n.para})"):
                    st.markdown(f"""
                    <div style='margin-bottom:0.5rem;'>
                        <span class='para-badge {para_class}'>{n.para}</span> &nbsp;
                        <span style='color:#869397; font-size:0.75rem;'>Created: {n.created}</span>
                    </div>
                    <div style='margin-bottom:0.75rem;'>{tags_html}</div>
                    <div style='background:#0b0e15; border:1px solid #233047; padding:0.75rem; font-size:0.85rem; line-height:1.6;'>
                        {n.body}
                    </div>
                    """, unsafe_allow_html=True)

                    # Quick actions per note
                    n_col1, n_col2 = st.columns(2)
                    with n_col1:
                        # Ask about this note
                        if st.button(f"🧠 Ask about this", key=f"ask_note_{n.id}", use_container_width=True):
                            st.session_state.prefill_query = f"Tell me more about: {n.summary}"
                            st.rerun()
                    with n_col2:
                        # Export single note
                        note_md = f"---\nid: {n.id}\npara: {n.para}\ntags: {', '.join(n.tags)}\ncreated: {n.created}\n---\n\n# {n.summary}\n\n{n.body}"
                        st.download_button(
                            "⬇ Export",
                            data=note_md.encode("utf-8"),
                            file_name=f"{n.id}.md",
                            mime="text/markdown",
                            key=f"dl_note_{n.id}",
                            use_container_width=True
                        )


# ==========================================
# TAB 4: CAPTURE QUEUE (NEW FEATURE)
# ==========================================
with tab_capture:
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;'>
        <div>
            <h2 style='margin:0; font-size:1.2rem;'>⚡ Live Ingestion Queue</h2>
            <div style='font-size:0.8rem; color:#869397;'>Real-time view of all captured items and their pipeline status.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    captures_info = get_raw_captures_info()

    if not captures_info:
        st.info("No captures in queue yet. Use the sidebar to capture a note, link or file.")
    else:
        # Filter tabs
        filter_cols = st.columns(5)
        all_c = len(captures_info)
        pending_c = sum(1 for c in captures_info if c["status"] == "pending")
        completed_c = sum(1 for c in captures_info if c["status"] == "completed")

        filters = {
            "all": f"All ({all_c})",
            "pending": f"Pending ({pending_c})",
            "completed": f"Completed ({completed_c})"
        }

        with filter_cols[0]:
            if st.button(filters["all"], key="filt_all", use_container_width=True,
                         type="primary" if st.session_state.queue_filter == "all" else "secondary"):
                st.session_state.queue_filter = "all"
                st.rerun()
        with filter_cols[1]:
            if st.button(filters["pending"], key="filt_pending", use_container_width=True,
                         type="primary" if st.session_state.queue_filter == "pending" else "secondary"):
                st.session_state.queue_filter = "pending"
                st.rerun()
        with filter_cols[2]:
            if st.button(filters["completed"], key="filt_completed", use_container_width=True,
                         type="primary" if st.session_state.queue_filter == "completed" else "secondary"):
                st.session_state.queue_filter = "completed"
                st.rerun()
        with filter_cols[3]:
            if pending_c > 0:
                if st.button(f"▶ Process {pending_c} Pending", use_container_width=True, type="primary", key="process_pending"):
                    with st.status(f"Processing {pending_c} captures...", expanded=True) as status:
                        st.write("1. Classifying notes (PARA)...")
                        process_classification()
                        st.write("2. Computing vectors & links...")
                        process_linking()
                        st.write("3. Rebuilding graph...")
                        build_graph()
                        status.update(label="All captures processed!", state="complete")
                    st.rerun()
        with filter_cols[4]:
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_queue"):
                st.rerun()

        st.markdown("<hr style='border:none; border-top:1px solid #233047; margin: 0.75rem 0;'>", unsafe_allow_html=True)

        # Filter captures
        active_filter = st.session_state.queue_filter
        if active_filter == "pending":
            visible = [c for c in captures_info if c["status"] == "pending"]
        elif active_filter == "completed":
            visible = [c for c in captures_info if c["status"] == "completed"]
        else:
            visible = captures_info

        # Table header
        hdr = st.columns([3, 1, 1, 1, 2])
        hdr[0].markdown("<span style='font-size:0.7rem; color:#869397; text-transform:uppercase;'>Payload / Source</span>", unsafe_allow_html=True)
        hdr[1].markdown("<span style='font-size:0.7rem; color:#869397; text-transform:uppercase;'>Type</span>", unsafe_allow_html=True)
        hdr[2].markdown("<span style='font-size:0.7rem; color:#869397; text-transform:uppercase;'>Stage</span>", unsafe_allow_html=True)
        hdr[3].markdown("<span style='font-size:0.7rem; color:#869397; text-transform:uppercase;'>Timestamp</span>", unsafe_allow_html=True)
        hdr[4].markdown("<span style='font-size:0.7rem; color:#869397; text-transform:uppercase;'>Preview</span>", unsafe_allow_html=True)

        st.markdown("<hr style='border:none; border-top:1px solid #233047; margin: 0.25rem 0;'>", unsafe_allow_html=True)

        for c in reversed(visible):  # Newest first
            type_color = {"note": "#4cd7f6", "link": "#4edea3", "file": "#c0c1ff"}.get(c["type"], "#869397")
            status_color = "#4edea3" if c["status"] == "completed" else "#4cd7f6"
            status_icon = "✓ Embedded" if c["status"] == "completed" else "⏳ Pending"

            row = st.columns([3, 1, 1, 1, 2])
            row[0].markdown(f"""
            <div style='font-family:"JetBrains Mono"; font-size:0.8rem;'>
                <span style='color:#ffffff;'>{c['id']}</span><br>
                <span style='color:#869397; font-size:0.7rem;'>{c['source'][:40]}</span>
            </div>""", unsafe_allow_html=True)
            row[1].markdown(f"<span style='color:{type_color}; font-family:\"JetBrains Mono\"; font-size:0.75rem; text-transform:uppercase;'>{c['type']}</span>", unsafe_allow_html=True)
            row[2].markdown(f"<span style='color:{status_color}; font-family:\"JetBrains Mono\"; font-size:0.75rem;'>{status_icon}</span>", unsafe_allow_html=True)
            row[3].markdown(f"<span style='color:#869397; font-family:\"JetBrains Mono\"; font-size:0.7rem;'>{c['timestamp'][:10]}</span>", unsafe_allow_html=True)
            row[4].markdown(f"<span style='color:#e1e2ec; font-family:\"JetBrains Mono\"; font-size:0.7rem;'>{c['preview'][:80]}...</span>", unsafe_allow_html=True)
            st.markdown("<hr style='border:none; border-top:1px solid #1d1f27; margin: 0.1rem 0;'>", unsafe_allow_html=True)


# ==========================================
# TAB 5: SEARCH VAULT (NEW FEATURE)
# ==========================================
with tab_search:
    st.markdown("""
    <div style='margin-bottom:1rem;'>
        <h2 style='margin:0; font-size:1.2rem;'>🔍 Semantic Vault Search</h2>
        <div style='font-size:0.8rem; color:#869397;'>Search through all vault notes using keyword or semantic similarity.</div>
    </div>
    """, unsafe_allow_html=True)

    search_col, mode_col = st.columns([5, 1])
    with search_col:
        search_query = st.text_input(
            "Search",
            placeholder="> Search notes by keyword, tag, or concept...",
            label_visibility="collapsed",
            key="vault_search_input"
        )
    with mode_col:
        search_mode = st.selectbox("Mode", ["Keyword", "Semantic"], label_visibility="collapsed", key="search_mode")

    if search_query:
        all_vault_notes = read_wiki_notes()

        if search_mode == "Keyword":
            # Fast local keyword search
            q_lower = search_query.lower()
            results = [
                n for n in all_vault_notes
                if q_lower in n.summary.lower()
                or q_lower in n.body.lower()
                or any(q_lower in t.lower() for t in n.tags)
                or q_lower in n.para.lower()
            ]
            st.markdown(f"<div style='font-size:0.8rem; color:#869397; margin-bottom:1rem;'>Found <b style='color:#4cd7f6;'>{len(results)}</b> keyword matches for '{search_query}'</div>", unsafe_allow_html=True)

        else:
            # Semantic vector search
            from lib.embeddings import embed_text, load_embeddings, cosine_similarity
            with st.spinner("Running semantic search..."):
                q_emb = embed_text(search_query)
                embeddings_dict = load_embeddings()
                if embeddings_dict:
                    scores = sorted(
                        [(nid, cosine_similarity(q_emb, emb)) for nid, emb in embeddings_dict.items()],
                        key=lambda x: x[1], reverse=True
                    )
                    note_map = {n.id: n for n in all_vault_notes}
                    results = []
                    for nid, score in scores[:10]:
                        if score > 0.15 and nid in note_map:
                            n = note_map[nid]
                            n._score = score
                            results.append(n)
                    st.markdown(f"<div style='font-size:0.8rem; color:#869397; margin-bottom:1rem;'>Found <b style='color:#4cd7f6;'>{len(results)}</b> semantic matches (cosine > 0.15) for '{search_query}'</div>", unsafe_allow_html=True)
                else:
                    results = []
                    st.warning("No embeddings found. Run the pipeline first.")

        if results:
            for n in results:
                para_class = f"para-{n.para}"
                score_badge = f" · {n._score*100:.1f}% match" if hasattr(n, '_score') else ""
                tags_html = " ".join([f"<span style='background:#10131a; color:#869397; padding:1px 5px; font-size:0.7rem; border:1px solid #233047;'>#{t}</span>" for t in n.tags])
                with st.expander(f"[{n.id}] {n.summary}{score_badge}"):
                    st.markdown(f"""
                    <div style='margin-bottom:0.5rem;'>
                        <span class='para-badge {para_class}'>{n.para}</span> &nbsp;
                        <span style='color:#4edea3; font-size:0.75rem; font-weight:700;'>
                            {'%.1f%%' % (n._score*100) + ' cosine match' if hasattr(n, '_score') else ''}
                        </span>&nbsp;
                        <span style='color:#869397; font-size:0.75rem;'>Created: {n.created}</span>
                    </div>
                    <div style='margin-bottom:0.75rem;'>{tags_html}</div>
                    <div style='background:#0b0e15; border:1px solid #233047; padding:0.75rem; font-size:0.85rem; line-height:1.6; max-height:200px; overflow:hidden;'>
                        {n.body[:500]}{'...' if len(n.body) > 500 else ''}
                    </div>
                    """, unsafe_allow_html=True)

                    s_col1, s_col2 = st.columns(2)
                    with s_col1:
                        if st.button(f"🧠 Ask about", key=f"search_ask_{n.id}", use_container_width=True):
                            st.session_state.prefill_query = f"Tell me about: {n.summary}"
                            st.rerun()
                    with s_col2:
                        note_md = f"---\nid: {n.id}\npara: {n.para}\ntags: {', '.join(n.tags)}\ncreated: {n.created}\n---\n\n# {n.summary}\n\n{n.body}"
                        st.download_button(
                            "⬇ Export",
                            data=note_md.encode("utf-8"),
                            file_name=f"{n.id}.md",
                            mime="text/markdown",
                            key=f"search_dl_{n.id}",
                            use_container_width=True
                        )
        else:
            st.info("No results found. Try a different query or run the pipeline to index more notes.")
    else:
        # Show vault overview when no search
        all_vault_notes = read_wiki_notes()
        if all_vault_notes:
            para_stats = {}
            for n in all_vault_notes:
                para_stats[n.para] = para_stats.get(n.para, 0) + 1

            cols = st.columns(len(para_stats) or 1)
            colors = {"Projects": "#4edea3", "Areas": "#c0c1ff", "Resources": "#4cd7f6", "Archives": "#a78bfa"}
            for i, (para, count) in enumerate(sorted(para_stats.items())):
                color = colors.get(para, "#869397")
                cols[i].markdown(f"""
                <div style='background:#191b23; border:1px solid #233047; border-left:3px solid {color}; padding:1rem; text-align:center;'>
                    <div style='font-family:"Space Grotesk"; font-size:2rem; font-weight:700; color:{color};'>{count}</div>
                    <div style='font-size:0.75rem; color:#869397; text-transform:uppercase;'>{para}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:1rem; font-size:0.85rem; color:#869397;'>Type a query above to search your vault.</div>", unsafe_allow_html=True)
