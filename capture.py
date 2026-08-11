import argparse
import uuid
import datetime
import os
import shutil

RAW_DIR = "raw"

def capture_content(content: str, is_file: bool = False):
    # Ensure the raw directory exists
    os.makedirs(RAW_DIR, exist_ok=True)
    
    # Generate timestamp and unique ID
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())
    
    if is_file:
        if not os.path.exists(content):
            print(f"Error: File '{content}' not found.")
            return
        
        filename = os.path.basename(content)
        ext = os.path.splitext(filename)[1]
        new_filename = f"{timestamp}_{unique_id}{ext}"
        dest_path = os.path.join(RAW_DIR, new_filename)
        
        # Copy the file to raw/
        shutil.copy2(content, dest_path)
        print(f"File captured successfully to {dest_path}")
    else:
        # Save text/URL as a markdown file
        new_filename = f"{timestamp}_{unique_id}.md"
        dest_path = os.path.join(RAW_DIR, new_filename)
        
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content + "\n")
            
        print(f"Note captured successfully to {dest_path}")

def main():
    parser = argparse.ArgumentParser(description="SecondSelf: Capture notes, URLs, or files to your raw directory.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", "--note", type=str, help="A text note or URL to capture")
    group.add_argument("-f", "--file", type=str, help="Path to a file to capture")
    
    args = parser.parse_args()
    
    if args.note:
        capture_content(args.note, is_file=False)
    elif args.file:
        capture_content(args.file, is_file=True)

if __name__ == "__main__":
    main()
