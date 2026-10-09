import os
import sys
from datetime import datetime
from lib.storage import read_raw_captures, write_wiki_note, load_index, save_index
from lib.models import WikiNote
from lib.llm import classify_content

def process_classification():
    index_data = load_index()
    raw_processed = index_data.setdefault("raw_processed", {})
    
    captures = read_raw_captures()
    if not captures:
        print("No raw captures found to classify.")
        return
        
    for meta, content in captures:
        if meta.id in raw_processed:
            continue
            
        print(f"Classifying {meta.id} ({meta.type})...")
        
        metadata = classify_content(content)
        
        category = metadata.get('para', 'Archives')
        if category not in ["Projects", "Areas", "Resources", "Archives"]:
            category = "Archives"
            
        tags = metadata.get('tags', [])
        summary = metadata.get('summary', '')
        
        # Create WikiNote
        wiki_note = WikiNote(
            id=meta.id.split('_')[-1] if '_' in meta.id else meta.id,
            raw_id=meta.id,
            para=category,
            tags=tags,
            summary=summary,
            created=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            links=[],
            body=content
        )
        
        write_wiki_note(wiki_note)
        raw_processed[meta.id] = True
        
        print(f"  -> wiki/{category}/{wiki_note.id}.md [{', '.join(tags)}] {summary}")
        
    save_index(index_data)

if __name__ == "__main__":
    process_classification()
