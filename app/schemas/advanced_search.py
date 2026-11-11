from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class AdvancedSearchRequest(BaseModel):
    """
    Schema for full-pipeline Advanced RAG Search request.
    """
    query: str = Field(..., description="User search query")
    top_k: int = Field(default=3, ge=1, le=20, description="Final number of context chunks to return")
    rrf_k: int = Field(default=60, ge=1, le=100, description="Reciprocal Rank Fusion constant")
    min_score_threshold: float = Field(default=0.0, description="Minimum cross-encoder relevance score cutoff")
    max_tokens: int = Field(default=500, ge=100, le=4000, description="Maximum total compressed token budget")
    enable_rerank: bool = Field(default=True, description="Enable Cross-Encoder reranking stage")
    enable_compression: bool = Field(default=True, description="Enable sentence compression and noise filtering")
    filename_filter: Optional[str] = Field(default=None, description="Optional filename metadata filter")


class AdvancedSearchResponse(BaseModel):
    """
    Schema for Advanced Search API response.
    """
    status: str
    query: str
    pipeline_stages_executed: List[str]
    total_results: int
    results: List[Dict[str, Any]]