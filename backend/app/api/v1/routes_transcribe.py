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
    initialize_index,
)

from app.services.nlp_service import run_ner_to_neo4j

router = APIRouter(tags=["Transcription"])
model = whisper.load_model("tiny")
TRANSCRIPTIONS = []

try:
    initialize_index()
    print("✅ FAISS index initialized inside routes_transcribe.")
except Exception as e:
    print(f"⚠️ Could not initialize FAISS in transcribe route: {e}")

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        ext = os.path.splitext(file.filename)[-1] or ".mp3"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        result = model.transcribe(tmp_path)
        text = (result.get("text") or "").strip()

        print("\n===== RAW TRANSCRIPT (first 800 chars) =====")
        print(text[:800])
        print("===========================================\n")

        try:
            os.remove(tmp_path)
        except Exception:
            pass

        ner_output = run_ner_to_neo4j("""Login Feature depends on Authentication Module and Session Management Component. The Login Feature must satisfy the security requirements and the usability requirements. Reporting Module is owned by Analytics Team and supported by Security Team. Test Case TC-101 and TC-102 validate the Authentication Module. API Rate Limit Constraint applies to the Payment Feature and the Reporting Module. The Distributed Ledger Architecture Design implements the Smart Contract Verification Feature and satisfies the immutability requirements. Audit Trail Component is derived from the Event Sourcing System. Checkout Feature refines the conversion requirements. DevOps Team is responsible for the deployment requirements""", always_restore_punct=True)
        rels = ner_output.get("relationships", [])
        ents = ner_output.get("entities", [])

        print(f"🔢 Entities: {len(ents)} | 🔗 Relationships: {len(rels)}")
        if len(rels) == 0:
            print("⚠️ Zero relationships — verify wording uses triggers like "
                  "'depends on', 'is owned by', 'supported by', 'must satisfy', 'applies to', "
                  "'validates', 'implements', 'refines', 'derived from', 'responsible for'.")

        entry = {
            "id": len(TRANSCRIPTIONS) + 1,
            "filename": file.filename,
            "text": text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ner": ner_output,
        }

        TRANSCRIPTIONS.append(entry)

        try:
            add_transcription_to_faiss(entry)
            print(f"✅ Added '{file.filename}' to FAISS index.")
        except Exception as e:
            print(f"⚠️ Could not update FAISS index: {e}")

        return {
            "message": f"✅ Transcription successful for {file.filename}",
            "entities_count": len(ents),
            "relationships_count": len(rels),
            "relationships_preview": rels[:25],
            "entry": entry,
        }

    except Exception as e:
        return {"error": f"❌ Transcription failed: {str(e)}"}

@router.get("/transcriptions")
async def get_all_transcriptions():
    return {"count": len(TRANSCRIPTIONS), "transcriptions": TRANSCRIPTIONS}

@router.get("/search")
async def search_transcriptions(
    q: str = Query(..., description="Search query for transcript similarity"),
    top_k: int = Query(3, description="Number of most similar results to return"),
):
    try:
        results = search_similar_transcripts(q, top_k=top_k)
        return {"query": q, "results": results}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

@router.post("/rebuild")
async def rebuild_faiss_index():
    try:
        from app.services.vector_service import build_index
        build_index(TRANSCRIPTIONS)
        return {"message": f"✅ Rebuilt FAISS index with {len(TRANSCRIPTIONS)} entries"}
    except Exception as e:
        return {"error": f"❌ Rebuild failed: {str(e)}"}
