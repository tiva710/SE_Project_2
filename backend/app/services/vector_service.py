# app/services/vector_service.py
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import faiss
# ... rest of your code
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# ======================================================
# 🔧 Config
# ======================================================
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
INDEX_PATH = os.path.join(DATA_DIR, "vector_index.faiss")
META_PATH = os.path.join(DATA_DIR, "vector_store.pkl")
MODEL_NAME = "all-MiniLM-L6-v2"

# ======================================================
# 🧠 Globals
# ======================================================
model = SentenceTransformer(MODEL_NAME)
index = None
metadata = []
_initialized = False

# ======================================================
# 🧩 Initialize index from disk (if exists)
# ======================================================
def initialize_index():
    global index, metadata, _initialized
    if _initialized:
        return
    
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
        try:
            index = faiss.read_index(INDEX_PATH)
            with open(META_PATH, "rb") as f:
                metadata = pickle.load(f)
            print(f"✅ Loaded existing FAISS index with {len(metadata)} entries")
        except Exception as e:
            print(f"⚠️ Failed to load FAISS index: {e}")
            index, metadata = None, []
    else:
        print("⚠️ No FAISS index found. Vector search will be disabled until built.")
    
    _initialized = True

# ======================================================
# 🧩 Build FAISS index from scratch (one-time)
# ======================================================
def build_index(transcripts):
    """
    transcripts = [{"text": "..."}, ...]
    """
    global index, metadata, _initialized
    os.makedirs(DATA_DIR, exist_ok=True)

    texts = [t["text"] for t in transcripts if t.get("text")]
    if not texts:
        print("⚠️ No text to build FAISS index.")
        return

    print(f"🔧 Building FAISS index for {len(texts)} transcripts...")
    embeddings = model.encode(texts, convert_to_numpy=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    metadata = transcripts

    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)
    print(f"✅ FAISS index built and saved ({len(metadata)} entries).")
    _initialized = True

# ======================================================
# 🧩 Incremental update (persistent) - THIS WAS MISSING!
# ======================================================
def add_transcription_to_faiss(entry):
    """
    Incrementally add a new transcription to FAISS index and persist.
    entry = {"text": "...", "filename": "..."}
    """
    global index, metadata, _initialized
    os.makedirs(DATA_DIR, exist_ok=True)

    # Ensure initialization happened first
    if not _initialized:
        initialize_index()

    text = entry.get("text")
    if not text:
        print("⚠️ Skipping empty transcription entry.")
        return

    emb = model.encode([text], convert_to_numpy=True)

    # Create new index if not yet initialized
    if index is None:
        print("⚙️ Creating new FAISS index...")
        index = faiss.IndexFlatL2(emb.shape[1])
        metadata = []

    # Add to FAISS + metadata
    index.add(emb)
    metadata.append(entry)

    # Save updated index + metadata to disk
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print(f"✅ Added new transcription to FAISS index ({len(metadata)} total)")

# ======================================================
# 🧩 Semantic search
# ======================================================
def search_similar_transcripts(query, top_k=3):
    global index, metadata, _initialized
    
    # Ensure initialization happened first
    if not _initialized:
        initialize_index()
    
    if index is None or len(metadata) == 0:
        print("⚠️ FAISS index not available. Returning empty results.")
        return []

    query_emb = model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(np.array(query_emb), top_k)

    results = []
    for idx in indices[0]:
        if idx < len(metadata):
            results.append(metadata[idx])
    return results
