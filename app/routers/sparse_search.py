from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services.bm25_service import BM25SearchService

router = APIRouter(prefix="/api/v1/search/sparse", tags=["Sparse Search"])

# Global in-memory instance for testing
bm25_service = BM25SearchService()


class SparseSearchRequest(BaseModel):
    """
    Schema for BM25 keyword search request.
    """
    query: str = Field(..., description="Keyword search query")
    top_k: int = Field(default=3, ge=1, le=20, description="Top K results to return")
    documents: List[str] = Field(..., description="List of document text strings to index dynamically")


class SparseSearchResponse(BaseModel):
    """
    Schema for BM25 search response.
    """
    status: str
    query: str
    total_results: int
    results: List[Dict[str, Any]]


@router.post("/bm25", response_model=SparseSearchResponse)
async def search_bm25_keywords(request: SparseSearchRequest):
    """
    Perform sparse keyword search using the BM25Okapi algorithm.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty."
        )

    try:
        chunks = [
            {"chunk_id": f"chunk-{idx}", "text": doc, "index": idx} 
            for idx, doc in enumerate(request.documents)
        ]
        bm25_service.build_index(chunks)
        results = bm25_service.search(query=request.query, top_k=request.top_k)

        return SparseSearchResponse(
            status="success",
            query=request.query,
            total_results=len(results),
            results=results
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BM25 search execution failed: {str(e)}"
        )