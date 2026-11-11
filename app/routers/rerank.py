from fastapi import APIRouter, HTTPException, status
from app.schemas.rerank import RerankRequest, RerankResponse, RerankedItem
from app.services.reranker_service import RerankerService

router = APIRouter(prefix="/api/v1/search/rerank", tags=["Cross-Encoder Reranker"])

# Lazy-loaded singleton instance
reranker_service: RerankerService = None


def get_reranker_service() -> RerankerService:
    global reranker_service
    if reranker_service is None:
        reranker_service = RerankerService()
    return reranker_service


@router.post("/rescore", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """
    Rerank a list of text document candidates against a query using a Cross-Encoder model.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    if not request.documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document list cannot be empty."
        )

    try:
        service = get_reranker_service()
        candidate_chunks = [
            {"index": idx, "text": doc} 
            for idx, doc in enumerate(request.documents)
        ]

        reranked_results = service.rerank(
            query=request.query,
            candidate_chunks=candidate_chunks,
            top_k=request.top_k
        )

        results = [RerankedItem(**item) for item in reranked_results]

        return RerankResponse(
            status="success",
            query=request.query,
            total_results=len(results),
            results=results
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reranking execution failed: {str(e)}"
        )