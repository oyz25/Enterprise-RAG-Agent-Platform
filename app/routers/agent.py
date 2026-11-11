from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent_router_service import AgentRouterService
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api/v1/agent", tags=["Multi-Agent Engine"])
agent_service = AgentRouterService()


@router.post("/process", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest, db: Session = Depends(get_db)):
    """
    Multi-Agent Router endpoint with PostgreSQL conversation state memory persistence.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    try:
        memory_service = MemoryService(db)

        # 1. Record incoming user message
        memory_service.add_message(
            session_id=request.session_id,
            role="user",
            content=request.query
        )

        # 2. Retrieve recent session context
        recent_history = memory_service.get_recent_history(
            session_id=request.session_id, 
            limit=6
        )

        # 3. Route and execute tool workflow
        execution_output = agent_service.route_and_execute(
            query=request.query,
            session_id=request.session_id
        )

        # 4. Extract assistant message string and persist to database
        res_data = execution_output["result"]
        assistant_content = str(res_data.get("response", res_data.get("message", res_data)))
        
        memory_service.add_message(
            session_id=request.session_id,
            role="assistant",
            content=assistant_content,
            intent=str(execution_output["intent"])
        )

        # Attach historical state to response payload
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