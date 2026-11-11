from fastapi import APIRouter, HTTPException, status
from app.schemas.advanced_search import AdvancedSearchRequest, AdvancedSearchResponse
from app.services.advanced_search_pipeline import AdvancedSearchPipelineService

router = APIRouter(prefix="/api/v1/search/advanced", tags=["Advanced Search Pipeline"])

# Singleton pipeline instance
pipeline_service = AdvancedSearchPipelineService()


@router.post("/execute", response_model=AdvancedSearchResponse)
async def execute_advanced_search(request: AdvancedSearchRequest):
    """
    Execute full Advanced RAG pipeline combining Hybrid Search, Cross-Encoder Reranking, and Context Compression.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query string cannot be empty."
        )

    try:
        pipeline_output = pipeline_service.execute_pipeline(
            query=request.query,
            top_k=request.top_k,
            rrf_k=request.rrf_k,
            min_score_threshold=request.min_score_threshold,
            max_tokens=request.max_tokens,
            enable_rerank=request.enable_rerank,
            enable_compression=request.enable_compression,
            filename_filter=request.filename_filter
        )

        return AdvancedSearchResponse(
            status="success",
            query=request.query,
            pipeline_stages_executed=pipeline_output["pipeline_stages_executed"],
            total_results=len(pipeline_output["results"]),
            results=pipeline_output["results"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced search pipeline failed: {str(e)}"
        )