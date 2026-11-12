import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.schemas.agent import AgentRequest, AgentResponse, AgentIntent
from app.services.agent_router_service import AgentRouterService
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api/v1/agent", tags=["Multi-Agent Engine"])
agent_service = AgentRouterService()


def _format_agent_response(intent: AgentIntent, result_data: Dict[str, Any]) -> str:
    """
    Convert structured tool execution outputs into clean, human-readable text.
    """
    if intent == AgentIntent.KNOWLEDGE_BASE:
        items = result_data.get("results", [])
        if not items:
            return "I searched the knowledge base, but found no matching documents for your query."
        lines = ["Here is what I found in your knowledge base:\n"]
        for idx, item in enumerate(items, start=1):
            text = item.get("compressed_text") or item.get("text", "")
            score = item.get("relevance_score", item.get("rrf_score", 0))
            lines.append(f"{idx}. {text.strip()} (Relevance: {score})")
        return "\n\n".join(lines)

    if intent == AgentIntent.WEB_SEARCH:
        items = result_data.get("results", [])
        if not items:
            return "No live web search results were found for that query."
        lines = ["Here are the top web search results:\n"]
        for idx, item in enumerate(items, start=1):
            lines.append(f"{idx}. **{item.get('title', 'Untitled')}**\n{item.get('snippet', '')}\nSource: {item.get('url', '')}")
        return "\n\n".join(lines)

    if intent == AgentIntent.CALCULATOR:
        if result_data.get("status") == "error":
            return f"Calculation error: {result_data.get('message', 'Invalid expression')}"
        return f"The result of `{result_data.get('expression')}` is **{result_data.get('result')}**."

    return str(result_data.get("response", "How can I assist you today?"))


@router.post("/process", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest, db: Session = Depends(get_db)):
    """
    Synchronous Multi-Agent Router endpoint with PostgreSQL conversation state persistence.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    try:
        memory_service = MemoryService(db)
        memory_service.add_message(
            session_id=request.session_id,
            role="user",
            content=request.query
        )

        recent_history = memory_service.get_recent_history(
            session_id=request.session_id,
            limit=6
        )

        execution_output = agent_service.route_and_execute(
            query=request.query,
            session_id=request.session_id
        )

        res_data = execution_output["result"]
        assistant_content = _format_agent_response(execution_output["intent"], res_data)

        memory_service.add_message(
            session_id=request.session_id,
            role="assistant",
            content=assistant_content,
            intent=str(execution_output["intent"].value)
        )

        response_payload = execution_output["result"]
        if isinstance(response_payload, dict):
            response_payload["session_history_count"] = len(recent_history)

        return AgentResponse(
            status="success",
            intent=execution_output["intent"],
            confidence_score=execution_output["confidence_score"],
            reasoning=execution_output["reasoning"],
            executed_action=execution_output["executed_action"],
            result=response_payload
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent routing execution failed: {str(e)}"
        )


@router.post("/stream")
async def stream_agent_request(request: AgentRequest):
    """
    Stream Multi-Agent intent routing, tool metadata, and formatted answer via Server-Sent Events (SSE).
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        db = SessionLocal()
        try:
            memory_service = MemoryService(db)
            session_id = request.session_id or "default_session"

            # 1. Persist user message
            memory_service.add_message(session_id=session_id, role="user", content=request.query)

            # 2. Execute routing and tool pipeline
            execution_output = agent_service.route_and_execute(
                query=request.query,
                session_id=session_id
            )

            intent: AgentIntent = execution_output["intent"]
            res_data = execution_output["result"]
            sources = res_data.get("results", []) if isinstance(res_data, dict) else []

            # 3. Emit metadata event (intent, action, structured sources)
            meta_payload = {
                "event": "metadata",
                "intent": intent.value,
                "executed_action": execution_output["executed_action"],
                "sources": sources,
            }
            yield f"data: {json.dumps(meta_payload)}\n\n"

            # 4. Format and stream response tokens
            formatted_text = _format_agent_response(intent, res_data)
            tokens = formatted_text.split(" ")
            for idx, token in enumerate(tokens):
                suffix = " " if idx < len(tokens) - 1 else ""
                yield f"data: {json.dumps({'event': 'text', 'delta': token + suffix})}\n\n"
                await asyncio.sleep(0.025)

            # 5. Persist final assistant response to PostgreSQL
            memory_service.add_message(
                session_id=session_id,
                role="assistant",
                content=formatted_text,
                intent=intent.value
            )

            # 6. Emit completion event
            yield f"data: {json.dumps({'event': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
        finally:
            db.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")