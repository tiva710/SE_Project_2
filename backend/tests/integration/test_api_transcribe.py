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
def reset_state(client, monkeypatch):  # ← Add 'client' parameter here!
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

    # Speed up: no punctuation model call
    try:
        from app.services import nlp_service as nlp
        monkeypatch.setattr(nlp, "_restore_punctuation", lambda t, force=True: t, raising=False)
    except Exception:
        pass

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
    assert "entry" in body
    entry = body["entry"]
    assert entry["filename"] == "meeting.wav"
    assert "ner" in entry
    ents = entry["ner"]["entities"]
    rels = entry["ner"]["relationships"]
    # Check for entities - they might be in different formats
    entity_names = [e.get("name") for e in ents if "name" in e]
    assert any("Login" in str(name) or "login" in str(name).lower() for name in entity_names), f"Expected Login entity, got: {entity_names}"
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

    r1 = client.post(f"{API}/transcribe", files=_file("a.wav"))
    r2 = client.post(f"{API}/transcribe", files=_file("b.wav"))
    id1 = r1.json()["entry"]["id"]
    id2 = r2.json()["entry"]["id"]
    assert id2 == id1 + 1

def test_transcribe_non_audio_extension_still_works(client, monkeypatch):
    import app.api.v1.routes_transcribe as rt
    
    monkeypatch.setattr(rt, "model", DummyModel("TC-200 validates Reporting Module."), raising=True)
    resp = client.post(f"{API}/transcribe", files=_file("notes.tmp", b"xyz", "application/octet-stream"))
    assert resp.status_code == 200
    data = resp.json()["entry"]
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
    data = resp.json()["entry"]
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

    resp = client.post(f"{API}/transcribe", files=_file("complex.wav"))
    assert resp.status_code == 200
    entry = resp.json()["entry"]
    ner = entry["ner"]
    # Collect entity names
    entity_names = {e.get("name") for e in ner.get("entities", []) if "name" in e}
    print(f"Found entities: {entity_names}")
    # Check for at least some expected entities (adjust based on your actual NER output)
    assert len(entity_names) > 0, f"Expected entities, got: {entity_names}"
    
    # Check for relationships
    rels = ner.get("relationships", [])
    print(f"Found relationships: {rels}")
    assert len(rels) > 0, f"Expected relationships, got: {rels}"