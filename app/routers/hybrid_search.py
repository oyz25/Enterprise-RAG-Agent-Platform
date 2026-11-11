from fastapi import APIRouter, HTTPException, status
from app.schemas.hybrid import HybridSearchRequest, HybridSearchResponse, HybridSearchResultItem
from app.services.hybrid_search import HybridSearchService

router = APIRouter(prefix="/api/v1/search/hybrid", tags=["Hybrid Search"])


@router.post("/rrf", response_model=HybridSearchResponse)
async def search_hybrid_rrf(request: HybridSearchRequest):
    """
    Execute Hybrid Search combining Qdrant Dense Vector Search and BM25 Keyword Search with RRF Reranking.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    try:
        hybrid_service = HybridSearchService()
        results_data = hybrid_service.search_hybrid(
            query=request.query,
            top_k=request.top_k,
            rrf_k=request.rrf_k,
            filename_filter=request.filename_filter
        )

        results = [HybridSearchResultItem(**item) for item in results_data]

        return HybridSearchResponse(
            status="success",
            query=request.query,
            total_results=len(results),
            results=results
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search failed: {str(e)}"
        )