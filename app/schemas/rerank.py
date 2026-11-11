from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RerankRequest(BaseModel):
    """
    Schema for document chunk reranking request.
    """
    query: str = Field(..., description="Target search query")
    top_k: int = Field(default=3, ge=1, le=20, description="Number of top reranked items to return")
    documents: List[str] = Field(..., description="List of document text candidate strings to rerank")


class RerankedItem(BaseModel):
    """
    Schema for an individual reranked item with relevance score.
    """
    index: int = Field(..., description="Original candidate document index")
    relevance_score: float = Field(..., description="Cross-encoder semantic relevance score")
    text: str = Field(..., description="Document text content")


class RerankResponse(BaseModel):
    """
    Schema for reranking operation response.
    """
    status: str
    query: str
    total_results: int
    results: List[RerankedItem]