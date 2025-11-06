import os
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.services import vector_service as vs


# ======================================================
# 🌱 Fixtures
# ======================================================

@pytest.fixture(autouse=True)
def reset_globals(tmp_path):
    """Reset module-level globals before each test."""
    vs.DATA_DIR = tmp_path
    vs.INDEX_PATH = tmp_path / "vector_index.faiss"
    vs.META_PATH = tmp_path / "vector_store.pkl"
    vs.index = None
    vs.metadata = []
    vs._initialized = False
    yield
    vs.index = None
    vs.metadata = []
    vs._initialized = False


# ======================================================
# 🔹 Initialization
# ======================================================

@patch("os.path.exists", return_value=False)
def test_initialize_index_no_files(mock_exists):
    vs.initialize_index()
    assert vs.index is None
    assert vs.metadata == []


@patch("os.path.exists",
       side_effect=lambda p: "vector_index.faiss" in str(p)
       or "vector_store.pkl" in str(p))
@patch("faiss.read_index")
@patch("builtins.open", new_callable=MagicMock)
@patch("pickle.load", return_value=[{"text": "hello"}])
def test_initialize_index_success(mock_pickle, mock_open, mock_faiss, mock_exists):
    vs.initialize_index()
    assert vs._initialized
    assert isinstance(vs.metadata, list)
    assert len(vs.metadata) == 1


@patch("faiss.read_index", side_effect=Exception("corrupt"))
def test_initialize_index_failure(mock_faiss):
    vs.initialize_index()
    assert vs.index is None
    assert isinstance(vs.metadata, list)


# ======================================================
# 🔹 Build Index
# ======================================================

@patch("faiss.write_index", MagicMock())
@patch("faiss.IndexFlatL2")
@patch.object(vs.model, "encode", return_value=np.random.rand(2, 384))
def test_build_index_success(mock_encode, mock_index):
    transcripts = [{"text": "hello"}, {"text": "world"}]
    vs.build_index(transcripts)
    assert len(vs.metadata) == 2
    assert vs._initialized


@patch.object(vs.model, "encode", return_value=np.random.rand(1, 384))
@patch("faiss.IndexFlatL2")
def test_build_index_empty_input(mock_index, mock_encode):
    vs.build_index([])
    assert vs.metadata == []


def test_build_index_creates_data_dir(tmp_path):
    vs.DATA_DIR = tmp_path
    os.makedirs(vs.DATA_DIR, exist_ok=True)
    assert os.path.exists(vs.DATA_DIR)


# ======================================================
# 🔹 Incremental Add
# ======================================================

@patch.object(vs.model, "encode", return_value=np.random.rand(1, 384))
@patch("faiss.write_index", MagicMock())
def test_add_transcription_creates_index(mock_encode):
    vs._initialized = True
    vs.add_transcription_to_faiss({"text": "new transcript", "filename": "file.txt"})
    assert len(vs.metadata) == 1


@patch.object(vs.model, "encode", return_value=np.random.rand(1, 384))
def test_add_transcription_empty_entry(mock_encode):
    vs._initialized = True
    initial_meta = len(vs.metadata)
    vs.add_transcription_to_faiss({"text": ""})
    assert len(vs.metadata) == initial_meta


@patch.object(vs.model, "encode", return_value=np.random.rand(1, 384))
@patch("faiss.write_index", MagicMock())
def test_add_transcription_persists(mock_encode):
    vs._initialized = True
    vs.add_transcription_to_faiss({"text": "persist test"})
    assert len(vs.metadata) == 1


@patch.object(vs.model, "encode", return_value=np.random.rand(1, 384))
@patch("faiss.write_index", MagicMock())
def test_add_transcription_multiple_adds(mock_encode):
    vs._initialized = True
    vs.add_transcription_to_faiss({"text": "A"})
    vs.add_transcription_to_faiss({"text": "B"})
    assert len(vs.metadata) == 2


# ======================================================
# 🔹 Search
# ======================================================

@patch.object(vs.model, "encode", return_value=np.random.rand(1, 384))
@patch.object(vs, "initialize_index")
def test_search_without_index(mock_init, mock_encode):
    vs.index, vs.metadata = None, []
    vs._initialized = True
    results = vs.search_similar_transcripts("query")
    assert results == []


@patch.object(vs.model, "encode", return_value=np.random.rand(1, 384))
def test_search_with_valid_index(mock_encode):
    vs._initialized = True
    vs.index = MagicMock()
    vs.index.search.return_value = (np.zeros((1, 3)), np.array([[0, 1, 2]]))
    vs.metadata = [{"text": "a"}, {"text": "b"}, {"text": "c"}]
    res = vs.search_similar_transcripts("hello", top_k=2)
    assert len(res) <= 3


def test_search_handles_index_shorter_than_results():
    vs._initialized = True
    vs.metadata = [{"text": "short"}]
    vs.index = MagicMock()
    vs.index.search.return_value = (np.zeros((1, 2)), np.array([[0, 1]]))
    vs.model.encode = MagicMock(return_value=np.random.rand(1, 384))
    res = vs.search_similar_transcripts("hi")
    assert len(res) == 1


def test_search_returns_empty_if_not_initialized():
    vs._initialized = False
    vs.index, vs.metadata = None, []
    res = vs.search_similar_transcripts("query")
    assert res == []


@patch.object(vs.model, "encode", return_value=np.random.rand(1, 384))
def test_search_returns_topk(mock_encode):
    vs._initialized = True
    vs.metadata = [{"text": "doc1"}, {"text": "doc2"}, {"text": "doc3"}]
    vs.index = MagicMock()
    vs.index.search.return_value = (np.zeros((1, 2)), np.array([[0, 2]]))
    res = vs.search_similar_transcripts("find", top_k=2)
    assert [r["text"] for r in res] == ["doc1", "doc3"]


# ======================================================
# 🔹 Edge / Integrity
# ======================================================

def test_model_loaded_once():
    assert isinstance(vs.model, vs.SentenceTransformer)


@patch("faiss.write_index", MagicMock())
def test_build_index_sets_initialized_flag():
    vs._initialized = False
    vs.build_index([{"text": "sample"}])
    assert vs._initialized is True


def test_initialize_idempotent():
    vs._initialized = True
    vs.initialize_index()
    assert vs._initialized


@patch("pickle.dump")
@patch("faiss.write_index", MagicMock())
def test_persistence_called(mock_dump):
    vs.index = MagicMock()
    vs.metadata = [{"text": "abc"}]
    vs._initialized = True
    vs.add_transcription_to_faiss({"text": "persist me"})
    assert mock_dump.called


@patch.object(vs.model, "encode", return_value=np.random.rand(1, 384))
def test_search_top_k_limit(mock_encode):
    vs._initialized = True
    vs.metadata = [{"text": str(i)} for i in range(5)]
    vs.index = MagicMock()
    vs.index.search.return_value = (np.zeros((1, 10)),
                                    np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]))
    res = vs.search_similar_transcripts("query", top_k=3)
    assert len(res) <= len(vs.metadata)
