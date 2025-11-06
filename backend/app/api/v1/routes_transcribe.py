# app/api/v1/routes_transcribe.py

from pprint import pprint
from fastapi import APIRouter, UploadFile, File, Query
import whisper
import tempfile
import os
import uuid
import hashlib
from datetime import datetime
from app.services.nlp_service import run_ner_to_neo4j

from app.services.vector_service import (
    add_transcription_to_faiss,
    search_similar_transcripts,
    initialize_index,
)

from app.services import nlp_service

# IMPORT the correct functions from neo4j_service
from app.services.neo4j_service import (
    write_to_db,
    fetch_graph_for_recording,
    recording_exists_by_audio_id,
)

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
    """
    Transcribes an uploaded audio file using Whisper,
    runs NER to extract entities/relationships,
    tags them with a unique recording_id and audio_id,
    writes the graph to Neo4j,
    persists transcription in FAISS vector store,
    and returns the conversation_id for scoped graph queries.
    """
    try:
        # Save uploaded file temporarily
        ext = os.path.splitext(file.filename)[-1] or ".mp3"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Compute audio_id from file bytes (stable, content-based)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        audio_id = hashlib.sha256(audio_bytes).hexdigest()

        # Transcribe
        result = model.transcribe(tmp_path)
        text = result.get("text", "").strip()
        print(text)

        # Cleanup temp
        try:
            os.remove(tmp_path)
        except Exception:
            pass

        # CHECK: Does this audio_id already exist in Neo4j?
        existing_recording_id = recording_exists_by_audio_id(audio_id)

        if existing_recording_id:
            # Audio already processed globally – fetch graph and return immediately
            print(f"✅ Duplicate audio detected: audio_id={audio_id}, reusing recording_id={existing_recording_id}")
            graph_data = fetch_graph_for_recording(existing_recording_id)
            return {
                "message": "⚠️ Duplicate audio detected; returning existing graph",
                "audio_id": audio_id,
                "conversation_id": existing_recording_id,
                "graph_data": graph_data,
                "skipped": True,
            }
        
        ner_output = run_ner_to_neo4j("""Login Feature depends on Authentication Module and Session Management Component. The Login Feature must satisfy the security requirements and the usability requirements. Reporting Module is owned by Analytics Team and supported by Security Team. Test Case TC-101 and TC-102 validate the Authentication Module. API Rate Limit Constraint applies to the Payment Feature and the Reporting Module. The Distributed Ledger Architecture Design implements the Smart Contract Verification Feature and satisfies the immutability requirements. Audit Trail Component is derived from the Event Sourcing System. Checkout Feature refines the conversion requirements. DevOps Team is responsible for the deployment requirements""", always_restore_punct=True)
        rels = ner_output.get("relationships", [])
        ents = ner_output.get("entities", [])

        print(f"🔢 Entities: {len(ents)} | 🔗 Relationships: {len(rels)}")
        if len(rels) == 0:
            print("⚠️ Zero relationships — verify wording uses triggers like "
                  "'depends on', 'is owned by', 'supported by', 'must satisfy', 'applies to', "
                  "'validates', 'implements', 'refines', 'derived from', 'responsible for'.")


        # # NEW AUDIO: Run NER
        # try:
        #     if hasattr(nlp_service, "run_ner_to_neo4j"):
        #         ner_output = nlp_service.run_ner_to_neo4j(text)
        #         pprint(ner_output)
        #     else:
        #         from app.services.nlp_service import RequirementsNERToNeo4j
        #         ner_output = RequirementsNERToNeo4j(use_spacy=True).process_text(text)
        # except Exception as ner_exc:
        #     ner_output = {"error": f"NER failed: {ner_exc}"}

        # Generate unique conversation_id for this extraction run
        conversation_id = f"rec_{uuid.uuid4().hex[:12]}"

        # TAG entities with both recording_id and audio_id
        if isinstance(ner_output, dict) and "entities" in ner_output:
            for entity in ner_output.get("entities", []):
                entity["properties"] = entity.get("properties", {})
                entity["properties"]["recording_id"] = conversation_id
                entity["properties"]["audio_id"] = audio_id
                entity["id"] = f"{entity.get('id','')}_{conversation_id}"

        # TAG relationships with both recording_id and audio_id
        if isinstance(ner_output, dict) and "relationships" in ner_output:
            for rel in ner_output.get("relationships", []):
                rel["properties"] = rel.get("properties", {})
                rel["properties"]["recording_id"] = conversation_id
                rel["properties"]["audio_id"] = audio_id
                rel["source"] = f"{rel.get('source','')}_{conversation_id}"
                rel["target"] = f"{rel.get('target','')}_{conversation_id}"

        # Write to Neo4j using MERGE (idempotent)
        neo4j_write_result = None
        try:
            if isinstance(ner_output, dict) and ("entities" in ner_output or "relationships" in ner_output):
                neo4j_write_result = write_to_db(ner_output)
                print(f"✅ Wrote to Neo4j: {neo4j_write_result}")
            else:
                print(f"⚠️ Skipping Neo4j write, unexpected NER output format: {type(ner_output)}")
        except Exception as neo4j_exc:
            neo4j_write_result = {"error": f"Neo4j write failed: {neo4j_exc}"}
            print(f"❌ Neo4j write failed: {neo4j_exc}")

        # Build structured entry
        entry = {
            "id": len(TRANSCRIPTIONS) + 1,
            "conversation_id": conversation_id,
            "audio_id": audio_id,
            "filename": file.filename,
            "text": text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ner": ner_output,
            "neo4j_write": neo4j_write_result,
        }

        # Save to memory
        TRANSCRIPTIONS.append(entry)

        # Persist to FAISS index
        try:
            add_transcription_to_faiss(entry)
            print(f"✅ Added '{file.filename}' to FAISS index.")
        except Exception as e:
            print(f"⚠️ Could not update FAISS index: {e}")

        # IMPORTANT: Fetch the graph data for the new recording
        graph_data = fetch_graph_for_recording(conversation_id)
        print(f"📊 Fetched graph data for new recording: {len(graph_data.get('nodes', []))} nodes")

        return {
            "message": f"✅ Transcription successful for {file.filename}",
            "audio_id": audio_id,
            "conversation_id": conversation_id,
            "graph_data": graph_data,  # ADDED: Return graph data for new uploads too
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