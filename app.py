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

st.set_page_config(page_title="SecondSelf", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
<style>
    /* Styling to match the screenshot */
    .title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: -1rem; }
    .subtitle { color: #8B949E; margin-bottom: 2rem; font-size: 0.95rem; }
    .section-header { font-size: 1.4rem; font-weight: 700; margin-bottom: 1rem; margin-top: 1.5rem; letter-spacing: -0.5px; }
    .stat-label { font-size: 0.85rem; color: #8B949E; margin-bottom: -0.5rem; font-weight: 600; }
    .stat-value { font-size: 1.8rem; font-weight: 600; margin-bottom: 1rem; color: #E2E8F0; }
    .sidebar-header { font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; margin-top: 1rem; }
    
    /* Make the top right button float nicely */
    .stButton>button { border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# Helper to get stats
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
        except:
            pass
    return notes, nodes, edges

notes_count, nodes_count, edges_count = get_stats()

# SIDEBAR
with st.sidebar:
    st.markdown("<div class='sidebar-header'>Capture</div>", unsafe_allow_html=True)
    capture_type = st.selectbox("Format", ["Quick note", "Web Link"], label_visibility="collapsed")
    
    if capture_type == "Quick note":
        st.markdown("<div style='font-size: 0.85rem; margin-bottom: 0.5rem; color: #E2E8F0;'>Quick note</div>", unsafe_allow_html=True)
        note_text = st.text_area("Capture a thought, task, or insight...", label_visibility="collapsed", height=100, placeholder="Capture a thought, task, or insight...")
        if st.button("Capture note", use_container_width=True):
            if note_text.strip():
                capture_note(note_text)
                st.success("Note captured!")
            else:
                st.error("Enter text.")
    else:
        st.markdown("<div style='font-size: 0.85rem; margin-bottom: 0.5rem; color: #E2E8F0;'>Web Link</div>", unsafe_allow_html=True)
        link_url = st.text_input("URL", label_visibility="collapsed", placeholder="https://...")
        link_notes = st.text_area("Notes", label_visibility="collapsed", placeholder="Optional context...", height=68)
        if st.button("Capture link", use_container_width=True):
            if link_url.strip():
                capture_link(link_url, link_notes)
                st.success("Link captured!")
            else:
                st.error("Enter URL.")
                
    st.markdown("<div class='sidebar-header' style='margin-top:2rem;'>Pipeline</div>", unsafe_allow_html=True)
    force_reprocess = st.checkbox("Force re-process")
    if st.button("Process new captures", type="primary", use_container_width=True):
        with st.status("Processing pipeline...", expanded=True):
            if force_reprocess:
                # Clear raw_processed to force full rebuild
                idx = load_index()
                idx["raw_processed"] = {}
                save_index(idx)
            st.write("Classifying notes...")
            process_classification()
            st.write("Linking concepts...")
            process_linking()
            st.write("Building graph...")
            build_graph()
        st.rerun()
        
    st.markdown("<div class='sidebar-header' style='margin-top:2rem;'>Stats</div>", unsafe_allow_html=True)
    st.markdown("<div class='stat-label'>Wiki notes</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='stat-value'>{notes_count}</div>", unsafe_allow_html=True)
    st.markdown("<div class='stat-label'>Graph nodes</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='stat-value'>{nodes_count}</div>", unsafe_allow_html=True)
    st.markdown("<div class='stat-label'>Graph edges</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='stat-value'>{edges_count}</div>", unsafe_allow_html=True)

# MAIN CONTENT
col1, col2 = st.columns([5, 1])
with col1:
    st.markdown("<h1 style='margin-bottom:0; padding-bottom:0;'>🧠 SecondSelf</h1>", unsafe_allow_html=True)
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Refresh graph", use_container_width=True):
        st.rerun()

st.markdown("<div class='subtitle'>Your personal AI second brain — capture, organize, explore, ask.</div>", unsafe_allow_html=True)

st.markdown("<div class='section-header'>Ask your brain</div>", unsafe_allow_html=True)

# We use columns for the input and Ask button
ask_col1, ask_col2 = st.columns([6, 1])
with ask_col1:
    query = st.text_input("Query", label_visibility="collapsed", placeholder="What are my career goals?")
with ask_col2:
    ask_btn = st.button("Ask", type="primary", use_container_width=True)

if ask_btn and query.strip():
    with st.spinner("Searching brain..."):
        result = ask(query)
        st.markdown(f"<div style='margin-top: 1rem; font-size: 1rem;'>{result.answer}</div>", unsafe_allow_html=True)
        
        if result.sources:
            st.markdown("<div style='margin-top: 1.5rem; font-weight: 600; font-size: 1.1rem; margin-bottom: 1rem;'>Sources</div>", unsafe_allow_html=True)
            for s in result.sources:
                badge = f"<span style='background-color: rgba(16, 185, 129, 0.1); color: #10B981; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.85em;'>{s['id']}</span>"
                st.markdown(f"• &nbsp;{badge} &nbsp;•&nbsp; {s['para']} &nbsp;•&nbsp; score **{s['relevance_score']:.3f}** &mdash; {s['summary']}", unsafe_allow_html=True)
        st.divider()

st.markdown("<div class='section-header'>Knowledge graph</div>", unsafe_allow_html=True)

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
    
    # We remove the "SecondSelf Brain" header from the embedded HTML so it looks seamless
    html_data = html_data.replace("<header>", "<header style='display:none;'>")
    
    # Embed seamlessly with rounded corners and border to match screenshot
    st.markdown('<div style="border: 1px solid #30363D; border-radius: 8px; overflow: hidden;">', unsafe_allow_html=True)
    components.html(html_data, height=600, scrolling=False)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Graph not built yet.")
