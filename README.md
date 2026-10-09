# SecondSelf

🧠 Your personal AI second brain — capture, organize, explore, ask.

![SecondSelf Screenshot](demo.pdf)

SecondSelf is a local-first, AI-powered knowledge management system. It automatically categorizes your notes, links related concepts using vector embeddings, visualizes them in an interactive graph, and lets you query your brain using RAG (Retrieval-Augmented Generation).

## Features
- **Capture:** Instantly ingest quick notes, URLs, and files.
- **Classify:** Automatically assign PARA categories (Projects, Areas, Resources, Archives), tags, and summaries using LLMs.
- **Link:** Automatically discover connections between your notes using vector embeddings.
- **Visualize:** Explore an interactive, force-directed graph of your entire knowledge base.
- **Ask:** Query your knowledge base in natural language.

## Architecture
See [Architecture Overview](doc/ARCHITECTURE.md) for detailed information on data models and component design.

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd secondself
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add your Groq API key:
   ```env
   GROQ_API_KEY=your_api_key_here
   ```

## Usage

### 1. Capture Knowledge
Use the CLI to capture text, URLs, or files:
```bash
python capture.py note "I want to learn more about RAG architectures."
python capture.py link "https://en.wikipedia.org/wiki/Vector_database"
```

### 2. Process Knowledge Base
Classify raw captures and build links:
```bash
python pipeline.py process
```

### 3. Build Graph
Generate the graph data for visualization:
```bash
python build_graph.py
```

### 4. Run the App
Launch the Streamlit interface to explore and ask questions:
```bash
streamlit run app.py
```

## Live Demo
https://secondself-demo.streamlit.app (Replace with your actual deployed URL)
