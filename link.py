import os
from lib.storage import read_wiki_notes, write_wiki_note
from lib.embeddings import load_model, save_embeddings, util

SIMILARITY_THRESHOLD = 0.75

def process_linking():
    print("Loading wiki notes...")
    notes = read_wiki_notes()
    if not notes:
        print("No wiki notes found.")
        return
        
    print(f"Found {len(notes)} notes. Loading embedding model (all-MiniLM-L6-v2)...")
    model = load_model()
    
    texts = [f"{n.id} {n.summary} {n.body}" for n in notes]
    embeddings = model.encode(texts, convert_to_tensor=True)
    
    # Save embeddings to dict for Phase 4
    embeddings_dict = {}
    for i, n in enumerate(notes):
        embeddings_dict[n.id] = embeddings[i]
    save_embeddings(embeddings_dict)
    
    # Compute cosine similarity
    cosine_scores = util.cos_sim(embeddings, embeddings)
    
    print("Finding relationships...")
    links_added = 0
    
    for i in range(len(notes)):
        new_links = []
        for j in range(len(notes)):
            if i == j:
                continue
            score = cosine_scores[i][j].item()
            if score >= SIMILARITY_THRESHOLD:
                new_links.append(notes[j].id)
                
        # Update note if links changed
        current_links = set(notes[i].links)
        new_links_set = set(new_links)
        
        if current_links != new_links_set:
            notes[i].links = list(new_links_set)
            
            # Auto-inject markdown links at the bottom of the body if not present
            for link in new_links_set:
                md_link = f"[[{link}]]"
                if md_link not in notes[i].body:
                    notes[i].body += f"\n\nRelated: {md_link}"
            
            write_wiki_note(notes[i])
            links_added += len(new_links_set) - len(current_links.intersection(new_links_set))
            print(f"[{notes[i].id}] linked to {len(new_links_set)} notes (threshold >= {SIMILARITY_THRESHOLD})")
            
    print(f"Auto-linking complete. Updated {links_added} links across {len(notes)} notes.")

if __name__ == "__main__":
    process_linking()
