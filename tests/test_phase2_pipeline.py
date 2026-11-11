import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_bm25_sparse_search():
    """
    Verify BM25 sparse keyword search endpoint returns ranked results.
    """
    payload = {
        "query": "FastAPI framework",
        "top_k": 2,
        "documents": [
            "FastAPI is a modern, fast web framework for building APIs with Python.",
            "PostgreSQL is an open-source relational database management system.",
            "Python is a versatile programming language."
        ]
    }
    response = client.post("/api/v1/search/sparse/bm25", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_results"] > 0
    assert "bm25_score" in data["results"][0]


def test_hybrid_rrf_search():
    """
    Verify Reciprocal Rank Fusion (RRF) hybrid search endpoint.
    """
    payload = {
        "query": "FastAPI REST API",
        "top_k": 2,
        "rrf_k": 60
    }
    response = client.post("/api/v1/search/hybrid/rrf", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data


def test_cross_encoder_rerank():
    """
    Verify Cross-Encoder rescore endpoint ranks relevant candidates highest.
    """
    payload = {
        "query": "FastAPI web framework",
        "top_k": 2,
        "documents": [
            "Python is a programming language.",
            "FastAPI is a high-performance web framework for building APIs with Python.",
            "SQLAlchemy is an Object Relational Mapper."
        ]
    }
    response = client.post("/api/v1/search/rerank/rescore", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["results"][0]["index"] == 1
    assert data["results"][0]["relevance_score"] > 0.0


def test_context_compression():
    """
    Verify noise filtering and context compression endpoint.
    """
    payload = {
        "query": "FastAPI web framework",
        "min_score_threshold": 0.0,
        "max_tokens": 500,
        "chunks": [
            {
                "chunk_id": "chunk-1",
                "relevance_score": 8.5,
                "text": "FastAPI is a high-performance web framework for building APIs with Python."
            },
            {
                "chunk_id": "chunk-2",
                "relevance_score": -10.0,
                "text": "PostgreSQL is a relational database."
            }
        ]
    }
    response = client.post("/api/v1/search/compress/filter", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["compressed_chunk_count"] == 1
    assert data["compressed_chunks"][0]["chunk_id"] == "chunk-1"


def test_advanced_search_pipeline():
    """
    Verify full end-to-end Advanced Search Pipeline orchestrator execution.
    """
    payload = {
        "query": "FastAPI REST API experience",
        "top_k": 3,
        "rrf_k": 60,
        "min_score_threshold": -5.0,
        "max_tokens": 500,
        "enable_rerank": True,
        "enable_compression": True
    }
    response = client.post("/api/v1/search/advanced/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["pipeline_stages_executed"]) == 3