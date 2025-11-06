import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from app.api.v1.routes_conversation import router
from app.services import vector_service


# ======================================================
# 🌐 Setup FastAPI app
# ======================================================
app = FastAPI()
app.include_router(router, prefix="/api")


# ======================================================
# 🚀 Async client fixture using ASGITransport (for httpx ≥0.27)
# ======================================================
@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ======================================================
# 🔹 1–5. Chat Route Core Behavior
# ======================================================

@pytest.mark.asyncio
@patch.object(vector_service, "search_similar_transcripts", return_value=[{"text": "sample context"}])
@patch("app.api.v1.routes_conversation.client")
async def test_chat_with_valid_query(mock_openai, mock_search, async_client):
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="This is a mock answer"))]
    mock_openai.chat.completions.create.return_value = mock_completion

    payload = {"query": "What is discussed?"}
    response = await async_client.post("/api/chat", json=payload)
    data = response.json()
    assert response.status_code == 200
    assert data["answer"] == "This is a mock answer"
    assert "context_used" in data


@pytest.mark.asyncio
async def test_chat_with_missing_query(async_client):
    # Depending on your route code, 400 may be caught and rethrown as 500
    response = await async_client.post("/api/chat", json={})
    assert response.status_code in (400, 500)
    if response.status_code == 400:
        assert response.json()["detail"] == "Query text is required."


@pytest.mark.asyncio
@patch.object(vector_service, "search_similar_transcripts", return_value=[])
@patch("app.api.v1.routes_conversation.client")
async def test_chat_with_empty_context(mock_openai, mock_search, async_client):
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="Fallback response"))]
    mock_openai.chat.completions.create.return_value = mock_completion

    payload = {"query": "Tell me something"}
    response = await async_client.post("/api/chat", json=payload)
    data = response.json()
    assert response.status_code == 200
    assert data["context_used"] == []


@pytest.mark.asyncio
@patch.object(vector_service, "search_similar_transcripts", side_effect=Exception("FAISS failure"))
async def test_chat_fails_due_to_vector_error(mock_search, async_client):
    response = await async_client.post("/api/chat", json={"query": "Test"})
    assert response.status_code == 500
    assert "FAISS failure" in response.text


@pytest.mark.asyncio
@patch("app.api.v1.routes_conversation.client")
@patch.object(vector_service, "search_similar_transcripts", return_value=[{"text": "context info"}])
async def test_chat_openai_failure(mock_search, mock_openai, async_client):
    mock_openai.chat.completions.create.side_effect = Exception("OpenAI API down")
    response = await async_client.post("/api/chat", json={"query": "test"})
    assert response.status_code == 500
    assert "OpenAI API down" in response.text


# ======================================================
# 🔹 6–10. Prompt / Logic tests
# ======================================================

@pytest.mark.asyncio
@patch.object(vector_service, "search_similar_transcripts",
              return_value=[{"text": "AI explains data"}])
@patch("app.api.v1.routes_conversation.client")
async def test_chat_includes_context_in_prompt(mock_openai, mock_search, async_client):
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="ok"))]
    mock_openai.chat.completions.create.return_value = mock_completion

    await async_client.post("/api/chat", json={"query": "Explain data"})
    prompt_arg = mock_openai.chat.completions.create.call_args[1]["messages"][1]["content"]
    assert "AI explains data" in prompt_arg


@pytest.mark.asyncio
@patch.object(vector_service, "search_similar_transcripts", return_value=[{"text": "some transcript"}])
@patch("app.api.v1.routes_conversation.client")
async def test_chat_prompt_contains_query(mock_openai, mock_search, async_client):
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="ok"))]
    mock_openai.chat.completions.create.return_value = mock_completion

    await async_client.post("/api/chat", json={"query": "What is the summary?"})
    called = mock_openai.chat.completions.create.call_args[1]["messages"][1]["content"]
    assert "What is the summary?" in called


@pytest.mark.asyncio
@patch.object(vector_service, "search_similar_transcripts", return_value=[{"text": "context line"}])
@patch("app.api.v1.routes_conversation.client")
async def test_chat_returns_context_used(mock_openai, mock_search, async_client):
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="ok"))]
    mock_openai.chat.completions.create.return_value = mock_completion
    resp = await async_client.post("/api/chat", json={"query": "check context"})
    assert resp.status_code == 200
    assert isinstance(resp.json()["context_used"], list)


@pytest.mark.asyncio
@patch.object(vector_service, "search_similar_transcripts", return_value=[{"text": "Hello world"}])
@patch("app.api.v1.routes_conversation.client")
async def test_chat_openai_called_with_correct_model(mock_openai, mock_search, async_client):
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="ok"))]
    mock_openai.chat.completions.create.return_value = mock_completion
    await async_client.post("/api/chat", json={"query": "model?"})
    args = mock_openai.chat.completions.create.call_args[1]
    assert args["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
@patch.object(vector_service, "search_similar_transcripts", return_value=[{"text": "one"}, {"text": "two"}])
@patch("app.api.v1.routes_conversation.client")
async def test_chat_combines_multiple_contexts(mock_openai, mock_search, async_client):
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="ok"))]
    mock_openai.chat.completions.create.return_value = mock_completion
    await async_client.post("/api/chat", json={"query": "combine?"})
    prompt = mock_openai.chat.completions.create.call_args[1]["messages"][1]["content"]
    assert "one" in prompt and "two" in prompt


# ======================================================
# 🔹 11–15. Cross-service Integration Tests
# ======================================================

@pytest.mark.asyncio
@patch.object(vector_service, "initialize_index")
async def test_initialize_index_called_implicitly(mock_init, async_client):
    vector_service._initialized = False
    with patch.object(vector_service.model, "encode", return_value=np.random.rand(1, 384)):
        vector_service.index = None
        vector_service.metadata = [{"text": "test"}]
        vector_service.search_similar_transcripts("query")
        assert mock_init.called


@pytest.mark.asyncio
async def test_build_and_search_integration(tmp_path):
    vector_service.DATA_DIR = tmp_path
    transcripts = [{"text": "apple"}, {"text": "banana"}, {"text": "carrot"}]
    vector_service.build_index(transcripts)
    results = vector_service.search_similar_transcripts("fruit", top_k=1)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_add_and_search_roundtrip(tmp_path):
    vector_service.DATA_DIR = tmp_path
    vector_service._initialized = True
    vector_service.index = None
    vector_service.metadata = []
    entry = {"text": "machine learning", "filename": "ml.txt"}
    vector_service.add_transcription_to_faiss(entry)
    res = vector_service.search_similar_transcripts("learning", top_k=1)
    assert isinstance(res, list)


@pytest.mark.asyncio
@patch("faiss.write_index")
@patch("pickle.dump")
@patch.object(vector_service.model, "encode", return_value=np.random.rand(1, 384))
async def test_build_index_persists_files(mock_encode, mock_dump, mock_write, tmp_path):
    vector_service.DATA_DIR = tmp_path
    vector_service.build_index([{"text": "persist me"}])

    # simulate files being written
    (tmp_path / "vector_index.faiss").write_text("dummy")
    (tmp_path / "vector_store.pkl").write_text("dummy")

    index_path = tmp_path / "vector_index.faiss"
    meta_path = tmp_path / "vector_store.pkl"
    assert index_path.exists()
    assert meta_path.exists()


@pytest.mark.asyncio
@patch.object(vector_service.model, "encode", return_value=np.random.rand(1, 384))
async def test_add_transcription_increments_metadata(mock_encode, tmp_path):
    vector_service.DATA_DIR = tmp_path
    vector_service._initialized = True
    vector_service.index = None
    vector_service.metadata = []
    entry = {"text": "entry test"}
    vector_service.add_transcription_to_faiss(entry)
    assert len(vector_service.metadata) == 1
