import os
import sys
import argparse
from datetime import datetime
from lib.models import CaptureMeta
from lib.storage import generate_capture_id, write_raw_capture, content_hash

def capture_note(text: str):
    if not text.strip():
        print("Error: Empty note text.")
        sys.exit(1)
        
    capture_id = generate_capture_id()
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    hash_val = content_hash(text)
    
    meta = CaptureMeta(
        id=capture_id,
        timestamp=timestamp,
        type="note",
        source="cli",
        content_hash=hash_val
    )
    
    res = write_raw_capture(meta, text)
    print(f"Captured -> {res.path}")

def capture_link(url: str, notes: str = ""):
    if not url.strip():
        print("Error: Empty link URL.")
        sys.exit(1)
        
    capture_id = generate_capture_id()
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"{url}\n\n{notes}"
    hash_val = content_hash(content)
    
    meta = CaptureMeta(
        id=capture_id,
        timestamp=timestamp,
        type="link",
        source=url,
        content_hash=hash_val
    )
    
    res = write_raw_capture(meta, content)
    print(f"Captured -> {res.path}")

def capture_file(path: str):
    if not os.path.exists(path):
        print(f"Error: File does not exist at {path}")
        sys.exit(1)
        
    capture_id = generate_capture_id()
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    with open(path, "rb") as f:
        content_bytes = f.read()
        
    # we convert bytes to a hashable string or just hash the bytes directly
    import hashlib
    hash_val = hashlib.sha256(content_bytes).hexdigest()
    
    original_filename = os.path.basename(path)
    
    meta = CaptureMeta(
        id=capture_id,
        timestamp=timestamp,
        type="file",
        source="local",
        original_filename=original_filename,
        content_hash=hash_val
    )
    
    res = write_raw_capture(meta, content_bytes)
    print(f"Captured -> {res.path}")

def main():
    parser = argparse.ArgumentParser(description="Capture data into SecondSelf raw folder.")
    subparsers = parser.add_subparsers(dest="command")
    
    note_parser = subparsers.add_parser("note", help="Capture a text note")
    note_parser.add_argument("text", type=str, help="The note text")
    
    link_parser = subparsers.add_parser("link", help="Capture a URL")
    link_parser.add_argument("url", type=str, help="The URL to capture")
    link_parser.add_argument("--notes", type=str, default="", help="Optional notes for the link")
    
    file_parser = subparsers.add_parser("file", help="Capture a file")
    file_parser.add_argument("path", type=str, help="Path to the file")
    
    args = parser.parse_args()
    
    if args.command == "note":
        capture_note(args.text)
    elif args.command == "link":
        capture_link(args.url, args.notes)
    elif args.command == "file":
        capture_file(args.path)
    else:
        # Interactive mode
        print("Interactive mode:")
        print("1. Note")
        print("2. Link")
        print("3. File")
        choice = input("Select type (1/2/3): ").strip()
        if choice == "1":
            text = input("Note text: ")
            capture_note(text)
        elif choice == "2":
            url = input("URL: ")
            notes = input("Optional notes: ")
            capture_link(url, notes)
        elif choice == "3":
            path = input("File path: ")
            capture_file(path)
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
