import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """
    Verify health check endpoint returns 200 OK.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chunking_process():
    """
    Verify text chunking engine generates valid chunks and metadata.
    """
    payload = {
        "text": "FastAPI is a modern, fast web framework for building APIs with Python. Qdrant is a vector database.",
        "filename": "test_doc.txt",
        "chunk_size": 150,
        "chunk_overlap": 20
    }
    response = client.post("/api/v1/chunking/process", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_chunks"] > 0
    assert "chunk_id" in data["chunks"][0]


def test_similarity_search():
    """
    Verify vector similarity search returns search results.
    """
    payload = {
        "query": "FastAPI web framework",
        "limit": 2
    }
    response = client.post("/api/v1/search/similarity", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data


def test_rag_streaming_endpoint():
    """
    Verify RAG streaming endpoint returns text/event-stream content.
    """
    payload = {
        "query": "FastAPI experience",
        "top_k": 2
    }
    response = client.post("/api/v1/rag/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]