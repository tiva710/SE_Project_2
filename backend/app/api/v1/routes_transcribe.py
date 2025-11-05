# app/api/v1/routes_transcribe.py

from pprint import pprint
from fastapi import APIRouter, UploadFile, File, Query
import whisper
import tempfile
import os
from datetime import datetime

from app.services.vector_service import (
    add_transcription_to_faiss,
    search_similar_transcripts,
    initialize_index,  # ✅ ensures persistence on startup
)

# NEW: import NER entrypoint
# Prefer a thin wrapper like run_ner_to_neo4j() if you've added it in nlp_service.
# Fallback builds the RequirementsNERToNeo4j engine inline if wrapper missing.
from app.services import nlp_service  # provides NER processing

# --------------------------------------------------------
# Initialize router
# --------------------------------------------------------
router = APIRouter(tags=["Transcription"])

# --------------------------------------------------------
# Initialize Whisper model once
# --------------------------------------------------------
model = whisper.load_model("tiny")

# --------------------------------------------------------
# Persistent in-memory store (mirrors FAISS metadata)
# --------------------------------------------------------
TRANSCRIPTIONS = []

# ✅ Load any existing FAISS metadata on startup
try:
    initialize_index()
    print("✅ FAISS index initialized inside routes_transcribe.")
except Exception as e:
    print(f"⚠️ Could not initialize FAISS in transcribe route: {e}")

# --------------------------------------------------------
# 🎧 Upload + Transcribe + NER
# --------------------------------------------------------
@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribes an uploaded audio file using Whisper,
    runs NER to extract entities/relationships,
    persists transcription in FAISS vector store,
    and keeps an in-memory reference.
    """
    try:
        # ✅ Save uploaded file temporarily
        ext = os.path.splitext(file.filename)[-1] or ".mp3"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # ✅ Run Whisper transcription
        result = model.transcribe(tmp_path)
        text = result.get("text", "").strip()
        print(text)

        # ✅ Clean up temporary file
        try:
            os.remove(tmp_path)
        except Exception:
            pass

        # ✅ Run NER immediately on the transcript
        try:
            # If a convenience wrapper exists in nlp_service:
            if hasattr(nlp_service, "run_ner_to_neo4j"):
                ner_output = nlp_service.run_ner_to_neo4j(text)
                pprint(ner_output)
                  # returns Neo4j-ready dict
            else:
                # Fallback: construct the engine directly
                from app.services.nlp_service import RequirementsNERToNeo4j
                ner_output = RequirementsNERToNeo4j(use_spacy=True).process_text(text)
        except Exception as ner_exc:
            ner_output = {"error": f"NER failed: {ner_exc}"}

        # ✅ Build structured entry
        entry = {
            "id": len(TRANSCRIPTIONS) + 1,
            "filename": file.filename,
            "text": text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ner": ner_output,  # include NER result
        }

        # ✅ Save to memory
        TRANSCRIPTIONS.append(entry)

        # ✅ Persist to FAISS index (with metadata including NER)
        try:
            add_transcription_to_faiss(entry)
            print(f"✅ Added '{file.filename}' to FAISS index.")
        except Exception as e:
            print(f"⚠️ Could not update FAISS index: {e}")

        return {
            "message": f"✅ Transcription successful for {file.filename}",
            "entry": entry,
        }

    except Exception as e:
        return {"error": f"❌ Transcription failed: {str(e)}"}

# --------------------------------------------------------
# 📋 Retrieve All Transcriptions
# --------------------------------------------------------
@router.get("/transcriptions")
async def get_all_transcriptions():
    """
    Returns all stored transcriptions (from memory).
    """
    return {"count": len(TRANSCRIPTIONS), "transcriptions": TRANSCRIPTIONS}

# --------------------------------------------------------
# 🔍 Semantic Search
# --------------------------------------------------------
@router.get("/search")
async def search_transcriptions(
    q: str = Query(..., description="Search query for transcript similarity"),
    top_k: int = Query(3, description="Number of most similar results to return"),
):
    """
    Searches FAISS vector store for semantically similar transcriptions.
    """
    try:
        results = search_similar_transcripts(q, top_k=top_k)
        return {"query": q, "results": results}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

# --------------------------------------------------------
# 🧩 (Optional) Manual FAISS Rebuild Endpoint
# --------------------------------------------------------
@router.post("/rebuild")
async def rebuild_faiss_index():
    """
    Rebuilds the FAISS index from all in-memory transcriptions.
    Useful for a full refresh after multiple uploads.
    """
    try:
        from app.services.vector_service import build_index
        build_index(TRANSCRIPTIONS)
        return {"message": f"✅ Rebuilt FAISS index with {len(TRANSCRIPTIONS)} entries"}
    except Exception as e:
        return {"error": f"❌ Rebuild failed: {str(e)}"}
