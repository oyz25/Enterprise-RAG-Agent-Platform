from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.schemas.rag import RAGQueryRequest
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/rag", tags=["RAG Generation Engine"])


@router.post("/stream")
async def stream_rag_answer(request: RAGQueryRequest):
    """
    Stream RAG answer token-by-token using Server-Sent Events (SSE) based on retrieved Qdrant context.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty."
        )

    rag_service = RAGService()

    return StreamingResponse(
        rag_service.generate_rag_stream(
            query=request.query,
            top_k=request.top_k,
            filename_filter=request.filename_filter
        ),
        media_type="text/event-stream"
    )