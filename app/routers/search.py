from fastapi import APIRouter, HTTPException, status
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/api/v1/search", tags=["Vector Search"])


@router.post("/similarity", response_model=SearchResponse)
async def search_similar_chunks(request: SearchRequest):
    """
    Perform vector similarity search over ingested document chunks with optional metadata filtering.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty."
        )

    try:
        vector_service = VectorStoreService()
        raw_results = vector_service.search_similarity(
            query_text=request.query,
            limit=request.limit,
            filename_filter=request.filename_filter
        )

        results = [SearchResultItem(**item) for item in raw_results]

        return SearchResponse(
            status="success",
            query=request.query,
            total_results=len(results),
            results=results
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search execution failed: {str(e)}"
        )