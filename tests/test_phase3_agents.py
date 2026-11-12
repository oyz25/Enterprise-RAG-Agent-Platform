import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_agent_direct_chat_and_tool_discovery():
    """
    Verify DIRECT_CHAT intent routing and registered ToolRegistry metadata exposure.
    """
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    payload = {
        "query": "Hello, who are you?",
        "session_id": session_id
    }
    response = client.post("/api/v1/agent/process", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["intent"] == "DIRECT_CHAT"
    assert "available_tools" in data["result"]
    tool_names = [t["name"] for t in data["result"]["available_tools"]]
    assert "calculator" in tool_names
    assert "web_search" in tool_names
    assert "knowledge_base" in tool_names


def test_agent_calculator_tool_execution():
    """
    Verify CALCULATOR intent classification and dynamic math tool evaluation.
    """
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    payload = {
        "query": "Calculate 45 * 12",
        "session_id": session_id
    }
    response = client.post("/api/v1/agent/process", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["intent"] == "CALCULATOR"
    assert data["result"]["status"] == "success"
    assert data["result"]["result"] == 540.0


def test_agent_knowledge_base_rag_routing():
    """
    Verify KNOWLEDGE_BASE_QUERY intent routes through the 3-stage Advanced RAG pipeline.
    """
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    payload = {
        "query": "What is the applicant's experience in FastAPI?",
        "session_id": session_id
    }
    response = client.post("/api/v1/agent/process", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["intent"] == "KNOWLEDGE_BASE_QUERY"
    assert data["result"]["status"] == "success"
    assert len(data["result"]["stages_executed"]) == 3


def test_postgresql_session_memory_persistence():
    """
    Verify multi-turn conversation history persists and increments in PostgreSQL.
    """
    session_id = f"memory_test_{uuid.uuid4().hex[:8]}"

    # Turn 1
    res1 = client.post("/api/v1/agent/process", json={
        "query": "Hello there",
        "session_id": session_id
    })
    assert res1.status_code == 200
    count1 = res1.json()["result"]["session_history_count"]

    # Turn 2 under the same session_id
    res2 = client.post("/api/v1/agent/process", json={
        "query": "Calculate 10 + 20",
        "session_id": session_id
    })
    assert res2.status_code == 200
    count2 = res2.json()["result"]["session_history_count"]

    assert count2 > count1
    assert count2 >= 3


def test_agent_sse_streaming_endpoint():
    """
    Verify /api/v1/agent/stream emits metadata, text tokens, and done SSE events.
    """
    session_id = f"stream_test_{uuid.uuid4().hex[:8]}"
    payload = {
        "query": "Calculate 8 * 8",
        "session_id": session_id
    }
    response = client.post("/api/v1/agent/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text
    assert '"event": "metadata"' in body
    assert '"intent": "CALCULATOR"' in body
    assert '"event": "text"' in body
    assert "64.0" in body
    assert '"event": "done"' in body