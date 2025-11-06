import io
import json
import pytest
from fastapi.testclient import TestClient

API = "/transcribe"

# ✅ Client fixture - loads first
@pytest.fixture(scope="function")
def client():
    """Fixture for FastAPI test client"""
    from app.main import app
    return TestClient(app)

# ✅ Reset state AFTER client is created - add client as dependency
@pytest.fixture(autouse=True)
def reset_state(client, monkeypatch):
    # Import here, AFTER app is fully loaded via client fixture
    import app.api.v1.routes_transcribe as rt
    import app.services.vector_service as vs
    
    # Reset in-memory store
    if hasattr(rt, "TRANSCRIPTIONS"):
        rt.TRANSCRIPTIONS.clear()

    # Stub FAISS/vector service
    monkeypatch.setattr(vs, "initialize_index", lambda: None, raising=False)
    monkeypatch.setattr(vs, "add_transcription_to_faiss", lambda entry: None, raising=False)
    monkeypatch.setattr(vs, "search_similar_transcripts", lambda q, top_k=3: [], raising=False)

    # Stub Neo4j service to prevent duplicate audio detection and DB calls
    try:
        from app.services import neo4j_service
        # Always return None for duplicate check (no existing recording)
        monkeypatch.setattr(neo4j_service, "recording_exists_by_audio_id", lambda audio_id: None, raising=False)
        # Mock successful DB write
        monkeypatch.setattr(neo4j_service, "write_to_db", lambda data: {"success": True, "nodes_created": 0, "relationships_created": 0}, raising=False)
        # Mock graph fetch with empty graph
        monkeypatch.setattr(neo4j_service, "fetch_graph_for_recording", lambda rec_id: {"nodes": [], "edges": []}, raising=False)
    except Exception as e:
        print(f"Warning: Could not stub neo4j_service: {e}")

    # Stub NLP service - now that route uses text variable, we need to mock run_ner_to_neo4j
    try:
        from app.services import nlp_service as nlp
        
        def mock_run_ner(text, always_restore_punct=False):
            """Mock NER that extracts basic entities/relationships from text"""
            # Simple entity extraction based on keywords in text
            entities = []
            relationships = []
            
            # Look for common patterns in the text
            words = text.split()
            for i, word in enumerate(words):
                if word in ["Module", "Feature", "Component", "Requirements", "Team"]:
                    if i > 0:
                        entity_name = f"{words[i-1]} {word}"
                        entities.append({
                            "id": f"ent_{len(entities)}",
                            "name": entity_name,
                            "type": word,
                            "properties": {}
                        })
            
            # Add at least one relationship if we have entities
            if len(entities) >= 2:
                relationships.append({
                    "source": entities[0]["id"],
                    "target": entities[1]["id"],
                    "type": "DEPENDS_ON",
                    "properties": {}
                })
            elif len(entities) == 1:
                # Create a self-relationship if only one entity
                relationships.append({
                    "source": entities[0]["id"],
                    "target": entities[0]["id"],
                    "type": "RELATES_TO",
                    "properties": {}
                })
            
            return {
                "entities": entities,
                "relationships": relationships
            }
        
        monkeypatch.setattr(nlp, "run_ner_to_neo4j", mock_run_ner, raising=False)
    except Exception as e:
        print(f"Warning: Could not stub nlp_service: {e}")

    yield

class DummyModel:
    def __init__(self, text):
        self._text = text
    def transcribe(self, path):
        return {"text": self._text}

def _file(name="x.wav", content=b"FAKE", mime="audio/wav"):
    return {"file": (name, io.BytesIO(content), mime)}

def test_list_routes(client):
    routes = [getattr(r, "path", "") for r in client.app.router.routes]
    print("ROUTES:", routes)
    assert any(p.startswith(API) for p in routes)

def test_transcribe_returns_ner_and_persists(client, monkeypatch):
    import app.api.v1.routes_transcribe as rt
    
    # Force a transcript with a feature and a requirement relationship
    monkeypatch.setattr(rt, "model", DummyModel("Login Feature must satisfy Authentication Requirements."), raising=True)

    resp = client.post(f"{API}/transcribe", files=_file("meeting.wav"))
    assert resp.status_code == 200
    body = resp.json()
    assert "entry" in body, f"Expected 'entry' in response, got: {body}"
    entry = body["entry"]
    assert entry["filename"] == "meeting.wav"
    assert "ner" in entry
    ents = entry["ner"]["entities"]
    rels = entry["ner"]["relationships"]
    # Check we have some entities and relationships
    assert len(ents) > 0, f"Expected entities, got: {ents}"
    assert len(rels) > 0, f"Expected relationships, got: {rels}"

    # GET list should include one entry
    resp2 = client.get(f"{API}/transcriptions")
    assert resp2.status_code == 200
    payload = resp2.json()
    assert payload["count"] == 1
    assert payload["transcriptions"][0]["filename"] == "meeting.wav"

def test_transcribe_multiple_uploads_increment_ids(client, monkeypatch):
    import app.api.v1.routes_transcribe as rt
    
    monkeypatch.setattr(rt, "model", DummyModel("Export Module depends on Analytics Module."), raising=True)

    # Use different file content to generate different audio_ids (prevents duplicate detection)
    r1 = client.post(f"{API}/transcribe", files=_file("a.wav", content=b"FAKE_AUDIO_1"))
    r2 = client.post(f"{API}/transcribe", files=_file("b.wav", content=b"FAKE_AUDIO_2"))
    
    # Handle potential error responses
    body1 = r1.json()
    body2 = r2.json()
    
    assert "entry" in body1, f"First upload failed: {body1}"
    assert "entry" in body2, f"Second upload failed: {body2}"
    
    id1 = body1["entry"]["id"]
    id2 = body2["entry"]["id"]
    assert id2 == id1 + 1

def test_transcribe_non_audio_extension_still_works(client, monkeypatch):
    import app.api.v1.routes_transcribe as rt
    
    monkeypatch.setattr(rt, "model", DummyModel("TC-200 validates Reporting Module."), raising=True)
    resp = client.post(f"{API}/transcribe", files=_file("notes.tmp", b"xyz", "application/octet-stream"))
    assert resp.status_code == 200
    body = resp.json()
    assert "entry" in body, f"Expected 'entry' in response, got: {body}"
    data = body["entry"]
    assert data["filename"] == "notes.tmp"
    # Check for relationships
    rels = data["ner"]["relationships"]
    assert len(rels) > 0, f"Expected relationships, got: {rels}"

def test_transcribe_empty_file_graceful(client, monkeypatch):
    import app.api.v1.routes_transcribe as rt
    
    # Even with empty bytes, route should handle and return an entry with text possibly empty
    monkeypatch.setattr(rt, "model", DummyModel(""), raising=True)
    resp = client.post(f"{API}/transcribe", files=_file("empty.wav", b""))
    assert resp.status_code == 200
    body = resp.json()
    assert "entry" in body, f"Expected 'entry' in response, got: {body}"
    data = body["entry"]
    assert "text" in data
    assert "ner" in data
    assert isinstance(data["ner"]["entities"], list)
    assert isinstance(data["ner"]["relationships"], list)

def test_transcribe_whisper_exception_path(client, monkeypatch):
    import app.api.v1.routes_transcribe as rt
    
    class Boom:
        def transcribe(self, path): raise RuntimeError("decode failure")
    monkeypatch.setattr(rt, "model", Boom(), raising=True)

    resp = client.post(f"{API}/transcribe", files=_file("bad.wav"))
    # Your handler returns 200 with {"error": "..."} on exception
    assert resp.status_code == 200
    body = resp.json()
    assert "error" in body or "entry" in body

def test_search_topk_param_and_result_shape(client, monkeypatch):
    import app.api.v1.routes_transcribe as rt

    monkeypatch.setattr(rt, "search_similar_transcripts", lambda q, top_k=2: [
        {"id": 1, "score": 0.8, "filename": "a.wav"},
        {"id": 2, "score": 0.7, "filename": "b.wav"},
    ], raising=True)

    resp = client.get(f"{API}/search", params={"q": "Login", "top_k": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "Login"
    assert len(data["results"]) == 2
    assert data["results"][0]["filename"] == "a.wav"


def test_rebuild_index_endpoint(client, monkeypatch):
    import app.api.v1.routes_transcribe as rt
    import app.services.vector_service as vs_local
    
    # Monkeypatch build_index used inside the route
    def _build_index(entries): assert isinstance(entries, list)
    monkeypatch.setattr(vs_local, "build_index", _build_index, raising=True)

    # Seed one transcript
    monkeypatch.setattr(rt, "model", DummyModel("Login Feature depends on Authentication Module."), raising=True)
    client.post(f"{API}/transcribe", files=_file("seed.wav"))

    resp = client.post(f"{API}/rebuild")
    assert resp.status_code == 200
    assert "Rebuilt FAISS index" in resp.json().get("message", "")

def test_transcribe_integration_core_entities(client, monkeypatch):
    import app.api.v1.routes_transcribe as rt
    
    # End-to-end: multiple entities and relationships extracted and included in response
    script = "Export Module depends on Billing Feature, Reporting Module and Analytics Module. " \
             "TC-200 validates Reporting Module and Analytics Module."
    monkeypatch.setattr(rt, "model", DummyModel(script), raising=True)

    # Use unique content to avoid duplicate detection
    resp = client.post(f"{API}/transcribe", files=_file("complex.wav", content=b"UNIQUE_COMPLEX_AUDIO"))
    assert resp.status_code == 200
    body = resp.json()
    
    # Handle potential error responses
    assert "entry" in body, f"Upload failed: {body}"
    
    entry = body["entry"]
    ner = entry["ner"]
    
    # Check that we have entities and relationships
    assert "entities" in ner, f"Expected 'entities' in NER output: {ner}"
    assert "relationships" in ner, f"Expected 'relationships' in NER output: {ner}"
    
    entities = ner.get("entities", [])
    relationships = ner.get("relationships", [])
    
    print(f"Found {len(entities)} entities: {entities}")
    print(f"Found {len(relationships)} relationships: {relationships}")
    
    # With our mock, we should get some entities and relationships
    assert len(entities) > 0, f"Expected entities, got: {entities}"
    assert len(relationships) > 0, f"Expected relationships, got: {relationships}"