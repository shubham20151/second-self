# SecondSelf Implementation Plan

This document outlines a phase-wise, step-by-step implementation plan for the SecondSelf project, combining the requirements from the problem statement and the design from the architecture document.

## Initial Setup
- [ ] **Create Repo Structure:** Initialize the `raw/` and `wiki/` directories.
- [ ] **Dependencies:** Create a `requirements.txt` containing dependencies such as `streamlit`, `sentence-transformers`, `streamlit-agraph`, `groq` or `openai`, and `networkx`.
- [ ] **Environment Variables:** Set up a `.env` file to store API keys (e.g., Groq API key).

---

## Phase 1: Data Ingestion (The Archivist)
**Goal:** Build the foundation to capture anything into one place.

### 1.1 `capture.py` Script
- [ ] Create a CLI script `capture.py` that accepts input (text strings, URLs, or file paths).
- [ ] Implement logic to assign a UUID and a timestamp to each captured item.
- [ ] Save the captured content as a plain text or markdown file in the `raw/` directory (e.g., `raw/{timestamp}_{uuid}.md`).

### 1.2 Testing Phase 1
- [ ] Capture at least 10 real pieces of your own information (notes, ideas, links).
- [ ] Verify that `raw/` is populated correctly.

---

## Phase 2: Processing & Organization (The Librarian)
**Goal:** Automate the filing and linking of raw captures using AI.

### 2.1 Auto-Classify (`classify.py`)
- [ ] Write a function to iterate over files in the `raw/` directory.
- [ ] Integrate an LLM (e.g., Llama 3 via Groq) to analyze the content.
- [ ] Prompt the LLM to output:
  - A category (Projects, Areas, Resources, Archives - PARA method).
  - A list of tags.
  - A one-line summary.
- [ ] Move the processed note to the `wiki/` directory, prepending the LLM-generated metadata (YAML frontmatter) to the file.

### 2.2 Auto-Link (`link.py`)
- [ ] Load a local embedding model using `sentence-transformers` (e.g., `all-MiniLM-L6-v2`).
- [ ] Compute embeddings for every note currently in the `wiki/` directory.
- [ ] Calculate the cosine similarity between the embeddings of all notes.
- [ ] For note pairs that exceed a predefined similarity threshold (e.g., > 0.75), auto-inject a markdown link (or a metadata reference) connecting them.
- [ ] Verify that 15+ real items are organized and linked in `wiki/`.

---

## Phase 3: Knowledge Representation (The Cartographer)
**Goal:** Convert the linked notes into a visual graph.

### 3.1 Graph Data Model (`build_graph.py`)
- [ ] Write a script that parses all notes in `wiki/`.
- [ ] Extract notes as **nodes** (using the note's UUID, title, and summary).
- [ ] Extract the relationships/links between notes as **edges**.
- [ ] Export the resulting graph structure to a clean JSON file (`graph.json`).

### 3.2 Testing Phase 3
- [ ] Inspect `graph.json` to ensure nodes and edges correctly represent the wiki folder.

---

## Phase 4: User Interface & Retrieval (The Oracle)
**Goal:** Enable natural language search and build a live UI.

### 4.1 Natural Language Search (`ask.py`)
- [ ] Build an `ask(query)` function.
- [ ] Compute the embedding of the user's `query`.
- [ ] Perform a vector search against the embeddings of notes in `wiki/` to find the most relevant notes.
- [ ] Construct a prompt containing the retrieved notes as context and pass it to the LLM to synthesize a natural language answer.

### 4.2 Web UI & Deployment (`app.py`)
- [ ] Create a Streamlit application.
- [ ] **Visual Graph:** Read `graph.json` and use `streamlit-agraph` (or a similar wrapper for Cytoscape/vis.js) to render an interactive, force-directed graph. Configure it to support zoom, drag, and hover tooltips showing note summaries.
- [ ] **Search Bar:** Integrate a chat/search interface in Streamlit that calls the `ask.py` function and displays the AI-synthesized answer.
- [ ] **Deployment:** Push the repository to GitHub and deploy the app to Streamlit Community Cloud or Hugging Face Spaces to get a public URL.

---

## Final Review
- [ ] Verify the complete end-to-end flow: Capture -> Classify -> Link -> Build Graph -> View/Ask in App.
- [ ] Ensure a clean `README.md` is present in the repository with setup and usage instructions.
