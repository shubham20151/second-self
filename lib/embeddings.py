import os
os.environ["USE_TF"] = "0"

import pickle
import torch
from sentence_transformers import SentenceTransformer, util

DATA_DIR = "data"
EMBEDDINGS_FILE = os.path.join(DATA_DIR, "embeddings.pkl")

# We defer loading the model to when it's first used to save memory
_model = None

def load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def embed_text(text: str) -> torch.Tensor:
    model = load_model()
    return model.encode(text, convert_to_tensor=True)

def cosine_similarity(a: torch.Tensor, b: torch.Tensor) -> float:
    if a.dim() == 1:
        a = a.unsqueeze(0)
    if b.dim() == 1:
        b = b.unsqueeze(0)
    return util.cos_sim(a, b).item()

def load_embeddings() -> dict:
    if not os.path.exists(EMBEDDINGS_FILE):
        return {}
    with open(EMBEDDINGS_FILE, 'rb') as f:
        return pickle.load(f)

def save_embeddings(embeddings_dict: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(EMBEDDINGS_FILE, 'wb') as f:
        pickle.dump(embeddings_dict, f)
