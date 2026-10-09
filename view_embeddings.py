import os
import pickle

DATA_DIR = "data"
EMBEDDINGS_FILE = os.path.join(DATA_DIR, "embeddings.pkl")

def main():
    if not os.path.exists(EMBEDDINGS_FILE):
        print(f"File not found: {EMBEDDINGS_FILE}")
        return

    with open(EMBEDDINGS_FILE, 'rb') as f:
        embeddings = pickle.load(f)

    if not embeddings:
        print("Embeddings dictionary is empty.")
        return

    print(f"Total embeddings found: {len(embeddings)}")
    print("-" * 50)
    
    for note_id, tensor in embeddings.items():
        # Display the shape of the tensor and a preview of the first 5 values
        shape = tuple(tensor.shape) if hasattr(tensor, 'shape') else "Unknown"
        
        # Convert tensor to a list for a readable preview if it's a PyTorch tensor
        if hasattr(tensor, 'tolist'):
            preview = tensor.tolist()
            # If it's a 1D tensor, preview the first 5 floats
            if isinstance(preview, list):
                if len(preview) > 0 and isinstance(preview[0], float):
                    preview_str = ", ".join(f"{v:.4f}" for v in preview[:5]) + " ..."
                else:
                    preview_str = str(preview)[:50] + "..."
        else:
            preview_str = str(tensor)[:50] + "..."
            
        print(f"Note ID : {note_id}")
        print(f"Shape   : {shape}")
        print(f"Preview : [{preview_str}]")
        print("-" * 50)

if __name__ == "__main__":
    main()
