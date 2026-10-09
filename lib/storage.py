import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from .models import CaptureMeta, CaptureResult, WikiNote

RAW_DIR = "raw"
WIKI_DIR = "wiki"
DATA_DIR = "data"
INDEX_FILE = os.path.join(DATA_DIR, "index.json")

def generate_capture_id() -> str:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    short_uuid = str(uuid.uuid4())[:8]
    return f"{timestamp}_{short_uuid}"

def content_hash(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def load_index() -> Dict[str, Any]:
    if not os.path.exists(INDEX_FILE):
        return {
            "raw_processed": {},
            "embeddings_version": "all-MiniLM-L6-v2",
            "last_graph_build": None
        }
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_index(index_data: Dict[str, Any]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2)

def write_raw_capture(meta: CaptureMeta, content: str) -> CaptureResult:
    os.makedirs(RAW_DIR, exist_ok=True)
    capture_dir = os.path.join(RAW_DIR, meta.id)
    os.makedirs(capture_dir, exist_ok=True)
    
    # Write meta.json
    with open(os.path.join(capture_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta.to_dict(), f, indent=2)
        
    # Write content
    ext = "txt" if meta.type != "file" else (meta.original_filename.split('.')[-1] if meta.original_filename and '.' in meta.original_filename else "bin")
    content_path = os.path.join(capture_dir, f"content.{ext}")
    
    if meta.type == "file" and not isinstance(content, str):
        # Handle binary if passed as bytes, though signature says str. We'll write as text otherwise.
        with open(content_path, "wb" if isinstance(content, bytes) else "w", encoding=None if isinstance(content, bytes) else "utf-8") as f:
            f.write(content)
    else:
        with open(content_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    return CaptureResult(id=meta.id, path=capture_dir, type=meta.type)

def read_raw_captures() -> List[Tuple[CaptureMeta, str]]:
    captures = []
    if not os.path.exists(RAW_DIR):
        return captures
        
    for item in os.listdir(RAW_DIR):
        capture_dir = os.path.join(RAW_DIR, item)
        if os.path.isdir(capture_dir):
            meta_path = os.path.join(capture_dir, "meta.json")
            if not os.path.exists(meta_path):
                continue
                
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_dict = json.load(f)
                meta = CaptureMeta(**meta_dict)
                
            # Find content file
            content = ""
            for f_name in os.listdir(capture_dir):
                if f_name.startswith("content."):
                    try:
                        with open(os.path.join(capture_dir, f_name), "r", encoding="utf-8") as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        content = f"[Binary File: {f_name}]"
                    break
            captures.append((meta, content))
    return captures

def write_wiki_note(note: WikiNote):
    cat_dir = os.path.join(WIKI_DIR, note.para)
    os.makedirs(cat_dir, exist_ok=True)
    
    yaml_frontmatter = "---\n"
    yaml_frontmatter += f"id: {note.id}\n"
    yaml_frontmatter += f"raw_id: {note.raw_id}\n"
    yaml_frontmatter += f"para: {note.para}\n"
    yaml_frontmatter += "tags:\n"
    for tag in note.tags:
        yaml_frontmatter += f"- {tag}\n"
    yaml_frontmatter += f"summary: {note.summary.replace('\"', '')}\n"
    yaml_frontmatter += f"created: '{note.created}'\n"
    yaml_frontmatter += "links:\n"
    for link in note.links:
        yaml_frontmatter += f"- {link}\n"
    if not note.links:
        yaml_frontmatter += "links: []\n"
    else:
        # replace the last "links:\n" logic if it had links
        pass # The loop above handles it if not empty, but wait, the empty case overwrites. It's fine.
        
    # Fix the links generation logic to be cleaner
    lines = ["---", f"id: {note.id}", f"raw_id: {note.raw_id}", f"para: {note.para}", "tags:"]
    for tag in note.tags:
        lines.append(f"- {tag}")
    lines.append(f"summary: {note.summary.replace('\"', '')}")
    lines.append(f"created: '{note.created}'")
    
    if note.links:
        lines.append("links:")
        for link in note.links:
            lines.append(f"- {link}")
    else:
        lines.append("links: []")
        
    lines.append("---")
    lines.append("")
    lines.append(note.body)
    
    dest_path = os.path.join(cat_dir, f"{note.id}.md")
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def read_wiki_notes() -> List[WikiNote]:
    notes = []
    if not os.path.exists(WIKI_DIR):
        return notes
        
    for root, _, files in os.walk(WIKI_DIR):
        for file in files:
            if not file.endswith(".md"):
                continue
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.startswith('---'):
                continue
                
            parts = content.split('---', 2)
            if len(parts) < 3:
                continue
                
            frontmatter = parts[1]
            body = parts[2].strip()
            
            # Parse frontmatter
            note_data = {
                "id": "", "raw_id": "", "para": "", "tags": [], 
                "summary": "", "created": "", "links": [], "body": body
            }
            
            lines = frontmatter.split('\n')
            current_list = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('id:'):
                    note_data['id'] = line.split('id:')[1].strip()
                elif line.startswith('raw_id:'):
                    note_data['raw_id'] = line.split('raw_id:')[1].strip()
                elif line.startswith('para:'):
                    note_data['para'] = line.split('para:')[1].strip()
                elif line.startswith('summary:'):
                    note_data['summary'] = line.split('summary:')[1].strip().strip("'\"")
                elif line.startswith('created:'):
                    note_data['created'] = line.split('created:')[1].strip().strip("'\"")
                elif line.startswith('tags:'):
                    current_list = note_data['tags']
                elif line.startswith('links:'):
                    current_list = note_data['links']
                    if '[]' in line:
                        current_list = None
                elif line.startswith('-') and current_list is not None:
                    current_list.append(line[1:].strip())
                    
            if note_data['id']:
                notes.append(WikiNote(**note_data))
                
    return notes
