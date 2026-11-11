from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class HybridSearchRequest(BaseModel):
    """
    Schema for Reciprocal Rank Fusion (RRF) Hybrid Search request.
    """
    query: str = Field(..., description="Search query string")
    top_k: int = Field(default=3, ge=1, le=20, description="Top K hybrid results to return")
    rrf_k: int = Field(default=60, ge=1, le=100, description="RRF constant parameter k")
    filename_filter: Optional[str] = Field(default=None, description="Optional filename filter")


class HybridSearchResultItem(BaseModel):
    """
    Schema for individual hybrid search result item with RRF score.
    """
    chunk_id: str
    rrf_score: float = Field(..., description="Reciprocal Rank Fusion merged score")
    dense_rank: Optional[int] = Field(default=None, description="Rank in Qdrant dense vector search")
    sparse_rank: Optional[int] = Field(default=None, description="Rank in BM25 sparse search")
    text: str
    metadata: Dict[str, Any]


class HybridSearchResponse(BaseModel):
    """
    Schema for hybrid search API response.
    """
    status: str
    query: str
    total_results: int
    results: List[HybridSearchResultItem]