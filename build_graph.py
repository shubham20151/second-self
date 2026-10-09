import os
import json
import re
from datetime import datetime
from lib.storage import read_wiki_notes, load_index, save_index
from lib.models import GraphNode, GraphEdge

DATA_DIR = "data"
GRAPH_FILE = os.path.join(DATA_DIR, "graph.json")

def build_graph():
    print("Reading wiki notes...")
    notes = read_wiki_notes()
    
    if not notes:
        print("No notes found to build the graph.")
        return
        
    nodes = []
    edges = []
    edge_set = set()
    
    link_pattern = re.compile(r'\[\[(.*?)\]\]')
    
    print(f"Processing {len(notes)} notes into nodes and edges...")
    for note in notes:
        # 1. Enrich nodes
        content_preview = note.body[:200] + ("..." if len(note.body) > 200 else "")
        node = GraphNode(
            id=note.id,
            label=note.summary if note.summary else note.id,
            para=note.para,
            tags=note.tags,
            summary=note.summary,
            content_preview=content_preview.replace('\n', ' '),
            group=note.para
        )
        nodes.append(node)
        
        # 2. Parse edges
        # Links from frontmatter
        all_links = set(note.links)
        
        # Links from body (wikilinks format [[id]])
        body_links = set(link_pattern.findall(note.body))
        all_links.update(body_links)
        
        for target_id in all_links:
            # 3. Deduplicate
            source = note.id
            target = target_id
            edge_key = tuple(sorted([source, target]))
            
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                # Ensure the target node actually exists (or will exist)
                # We'll just assume it exists for the graph representation
                edge = GraphEdge(
                    source=source,
                    target=target,
                    weight=1.0,
                    type="related"
                )
                edges.append(edge)
                
    # 4. Export to graph.json
    graph_data = {
        "nodes": [n.to_dict() for n in nodes],
        "edges": [e.to_dict() for e in edges],
        "metadata": {
            "generated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    }
    
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(GRAPH_FILE, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)
        
    print(f"Graph built successfully! Saved to {GRAPH_FILE}")
    print(f"Nodes: {len(nodes)} | Edges: {len(edges)}")
    
    # Update index.json
    index_data = load_index()
    index_data["last_graph_build"] = graph_data["metadata"]["generated_at"]
    save_index(index_data)

if __name__ == "__main__":
    build_graph()
