from fastapi import APIRouter, HTTPException, status
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent_router_service import AgentRouterService

router = APIRouter(prefix="/api/v1/agent", tags=["Multi-Agent Engine"])
agent_service = AgentRouterService()


@router.post("/process", response_model=AgentResponse)
async def process_agent_request(request: AgentRequest):
    """
    Multi-Agent Router endpoint to classify user intent and execute appropriate agent workflows.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    try:
        execution_output = agent_service.route_and_execute(
            query=request.query,
            session_id=request.session_id
        )

        return AgentResponse(
            status="success",
            intent=execution_output["intent"],
            confidence_score=execution_output["confidence_score"],
            reasoning=execution_output["reasoning"],
            executed_action=execution_output["executed_action"],
            result=execution_output["result"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent routing execution failed: {str(e)}"
        )