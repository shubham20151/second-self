import streamlit as st
import os
import json
from ask import ask
from capture import capture_note, capture_link
from classify import process_classification
from link import process_linking
from build_graph import build_graph
import streamlit.components.v1 as components
from lib.storage import read_wiki_notes, load_index, save_index
from lib.llm import _get_client, _get_model

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

    /* Overall font and dark background */
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

    /* Headers with Space Grotesk */
    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.02em !important;
        color: #ffffff !important;
    }

    /* Buttons - Cyber Brutalist (0px radius) */
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

    /* Tabs Styling */
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
</style>
""", unsafe_allow_html=True)

# Helper function to get database & graph statistics
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

notes_count, nodes_count, edges_count = get_stats()

# Detect active LLM model
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
            <div style='font-size:0.7rem; color:#4cd7f6; letter-spacing:0.1em; text-transform:uppercase;'>Cortex Node v2.4</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Ingestion Center
    st.markdown("<div style='font-size:0.75rem; color:#869397; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;'>Capture Stream</div>", unsafe_allow_html=True)
    capture_fmt = st.selectbox("Type", ["Quick Note", "Web Link"], label_visibility="collapsed")
    
    if capture_fmt == "Quick Note":
        note_input = st.text_area("Thought", placeholder="Capture a thought, task, or insight...", label_visibility="collapsed", height=90)
        if st.button("Capture Note", use_container_width=True, type="primary"):
            if note_input.strip():
                capture_note(note_input)
                st.success("Captured to brain stream!")
                st.rerun()
            else:
                st.error("Text cannot be empty.")
    else:
        url_input = st.text_input("URL", placeholder="https://...", label_visibility="collapsed")
        notes_context = st.text_area("Context", placeholder="Optional context...", label_visibility="collapsed", height=65)
        if st.button("Ingest Link", use_container_width=True, type="primary"):
            if url_input.strip():
                capture_link(url_input, notes_context)
                st.success("Web link ingested!")
                st.rerun()
            else:
                st.error("Please enter a valid URL.")

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

# Top Telemetry Header
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
tab_ask, tab_graph, tab_para, tab_stitch = st.tabs([
    "🧠  ASK YOUR BRAIN",
    "🕸️  KNOWLEDGE GRAPH",
    "📁  PARA VAULT",
    "🎨  STITCH PROTOTYPE UI"
])

# ------------------------------------------
# TAB 1: ASK YOUR BRAIN (RAG SYNTHESIS)
# ------------------------------------------
with tab_ask:
    st.markdown("""
    <div class='stitch-card'>
        <div class='stitch-card-header'>
            <span style='font-size:0.75rem; text-transform:uppercase; color:#869397;'>RAG Natural Language Synthesis Engine</span>
            <span style='font-size:0.75rem; color:#4edea3;'>Top_K=5 · Temperature 0.10</span>
        </div>
    """, unsafe_allow_html=True)

    col_q, col_btn = st.columns([6, 1])
    with col_q:
        q_val = st.text_input("Query", placeholder="> What are my current tasks and project priorities?", label_visibility="collapsed")
    with col_btn:
        ask_trigger = st.button("Synthesize", type="primary", use_container_width=True)

    # Quick prompt trajectories
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
        with st.spinner("Executing neural retrieval & LLM synthesis..."):
            res = ask(q_val)
            
            # Answer Box
            st.markdown(f"""
            <div class='stitch-card' style='border-left: 3px solid #4cd7f6;'>
                <div class='stitch-card-header'>
                    <div style='display:flex; align-items:center; gap:0.5rem;'>
                        <span style='color:#4cd7f6;'>⚡</span>
                        <span style='font-weight:700; color:#ffffff;'>Synthesized Cognitive Conclusion</span>
                    </div>
                    <span style='font-size:0.75rem; color:#4edea3; font-family:"JetBrains Mono";'>Grounded from Vault</span>
                </div>
                <div style='font-size:1.05rem; line-height:1.7; color:#f1f5f9; padding:0.5rem 0;'>
                    {res.answer}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Sources Section
            if res.sources:
                st.markdown("<div style='font-size:0.85rem; font-weight:700; text-transform:uppercase; color:#869397; margin:1rem 0 0.5rem 0;'>Retrieved Semantic Evidence</div>", unsafe_allow_html=True)
                src_cols = st.columns(min(len(res.sources), 3))
                for idx_s, s in enumerate(res.sources):
                    col_target = src_cols[idx_s % len(src_cols)]
                    with col_target:
                        para_class = f"para-{s.get('para', 'Archives')}"
                        st.markdown(f"""
                        <div class='stitch-card' style='height:100%;'>
                            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;'>
                                <span class='citation-badge'>[{s['id']}]</span>
                                <span class='para-badge {para_class}'>{s.get('para', 'Note')}</span>
                            </div>
                            <div style='font-weight:600; color:#ffffff; font-size:0.9rem; margin-bottom:0.5rem;'>{s['summary']}</div>
                            <div style='display:flex; justify-content:space-between; font-size:0.75rem; color:#869397; margin-top:auto;'>
                                <span>Cosine Match</span>
                                <span style='color:#4edea3; font-weight:700;'>{s['relevance_score']*100:.1f}%</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: KNOWLEDGE GRAPH
# ------------------------------------------
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

# ------------------------------------------
# TAB 3: PARA VAULT EXPLORER
# ------------------------------------------
with tab_para:
    all_notes = read_wiki_notes()
    if not all_notes:
        st.info("No wiki notes found yet in the vault.")
    else:
        para_categories = ["All", "Projects", "Areas", "Resources", "Archives"]
        sel_cat = st.selectbox("Filter Category", para_categories, horizontal=True)

        filtered = [n for n in all_notes if sel_cat == "All" or n.para == sel_cat]
        st.markdown(f"<div style='font-size:0.8rem; color:#869397; margin-bottom:1rem;'>Showing {len(filtered)} of {len(all_notes)} vault artifacts.</div>", unsafe_allow_html=True)

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

# ------------------------------------------
# TAB 4: STITCH PROTOTYPE UI PREVIEW
# ------------------------------------------
with tab_stitch:
    st.markdown("""
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;'>
        <div style='font-size:0.85rem; color:#869397;'>Preview the high-fidelity standalone Stitch screens directly inside Streamlit:</div>
    </div>
    """, unsafe_allow_html=True)

    stitch_screens = {
        "Ask Your Brain (RAG Q&A)": "stitch_ui/ask.html",
        "Visual Knowledge Graph": "stitch_ui/graph.html",
        "Capture & Pipeline Deck": "stitch_ui/capture.html",
        "PARA Organization Explorer": "stitch_ui/para.html"
    }

    screen_choice = st.radio("Choose Stitch Screen", list(stitch_screens.keys()), horizontal=True)
    target_file = stitch_screens[screen_choice]

    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            stitch_html = f.read()
        st.markdown('<div style="border:1px solid #233047; overflow:hidden; margin-top:0.5rem;">', unsafe_allow_html=True)
        components.html(stitch_html, height=800, scrolling=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error(f"File not found: {target_file}")
