from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SearchRequest(BaseModel):
    """
    Schema for vector similarity search request.
    """
    query: str = Field(..., description="Natural language search query")
    limit: int = Field(default=3, ge=1, le=20, description="Top K results to return")
    filename_filter: Optional[str] = Field(default=None, description="Optional filename filter")


class SearchResultItem(BaseModel):
    """
    Schema for an individual search result chunk.
    """
    chunk_id: str
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    text: str
    chunk_index: int
    token_count: int
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """
    Schema for search operation response.
    """
    status: str
    query: str
    total_results: int
    results: List[SearchResultItem]