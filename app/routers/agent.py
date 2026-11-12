import json
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.core.security import verify_api_key, validate_user_input
from app.schemas.agent import AgentRequest, AgentResponse, AgentIntent
from app.services.agent_router_service import AgentRouterService
from app.services.memory_service import MemoryService
from app.services.llm_synthesizer import LLMSynthesizerService

router = APIRouter(prefix="/api/v1/agent", tags=["Multi-Agent Engine"])
agent_service = AgentRouterService()
synthesizer_service = LLMSynthesizerService()


@router.post("/process", response_model=AgentResponse)
async def process_agent_request(
    request: AgentRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """
    Multi-Agent Router endpoint with API key auth, input guardrails, PostgreSQL memory,
    and citation-grounded synthesis.
    """
    validated_query = validate_user_input(request.query)

    try:
        memory_service = MemoryService(db)
        session_id = request.session_id or "default_session"

        prior_history = memory_service.get_recent_history(session_id=session_id, limit=6)

        memory_service.add_message(
            session_id=session_id,
            role="user",
            content=validated_query
        )

        execution_output = agent_service.route_and_execute(
            query=validated_query,
            session_id=session_id
        )

        intent: AgentIntent = execution_output["intent"]
        res_data = execution_output["result"]

        synthesis = synthesizer_service.synthesize(
            query=validated_query,
            intent=intent,
            result_data=res_data,
            history=prior_history,
        )

        memory_service.add_message(
            session_id=session_id,
            role="assistant",
            content=synthesis["answer"],
            intent=intent.value
        )

        updated_history = memory_service.get_recent_history(session_id=session_id, limit=10)

        response_payload = dict(res_data) if isinstance(res_data, dict) else {"raw": res_data}
        response_payload["synthesized_answer"] = synthesis["answer"]
        response_payload["citations"] = synthesis["citations"]
        response_payload["synthesis_mode"] = synthesis["synthesis_mode"]
        response_payload["session_history_count"] = len(updated_history)

        return AgentResponse(
            status="success",
            intent=intent,
            confidence_score=execution_output["confidence_score"],
            reasoning=execution_output["reasoning"],
            executed_action=execution_output["executed_action"],
            result=response_payload
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent routing execution failed: {str(e)}"
        )


@router.post("/stream")
async def stream_agent_request(
    request: AgentRequest,
    _: str = Depends(verify_api_key),
):
    """
    Stream Multi-Agent metadata, citations, and grounded synthesis tokens via SSE.
    """
    validated_query = validate_user_input(request.query)

    async def event_generator() -> AsyncGenerator[str, None]:
        db = SessionLocal()
        try:
            memory_service = MemoryService(db)
            session_id = request.session_id or "default_session"

            prior_history = memory_service.get_recent_history(session_id=session_id, limit=6)
            memory_service.add_message(session_id=session_id, role="user", content=validated_query)

            execution_output = agent_service.route_and_execute(
                query=validated_query,
                session_id=session_id
            )

            intent: AgentIntent = execution_output["intent"]
            res_data = execution_output["result"]

            synthesis = synthesizer_service.synthesize(
                query=validated_query,
                intent=intent,
                result_data=res_data,
                history=prior_history,
            )

            meta_payload = {
                "event": "metadata",
                "intent": intent.value,
                "executed_action": execution_output["executed_action"],
                "synthesis_mode": synthesis["synthesis_mode"],
                "citations": synthesis["citations"],
                "sources": synthesis["citations"],
            }
            yield f"data: {json.dumps(meta_payload)}\n\n"

            formatted_text = synthesis["answer"]
            tokens = formatted_text.split(" ")
            for idx, token in enumerate(tokens):
                suffix = " " if idx < len(tokens) - 1 else ""
                yield f"data: {json.dumps({'event': 'text', 'delta': token + suffix})}\n\n"
                await asyncio.sleep(0.02)

            memory_service.add_message(
                session_id=session_id,
                role="assistant",
                content=formatted_text,
                intent=intent.value
            )

            yield f"data: {json.dumps({'event': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
        finally:
            db.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")