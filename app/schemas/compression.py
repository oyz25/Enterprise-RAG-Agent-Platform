from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class CompressionRequest(BaseModel):
    """
    Schema for context compression and noise filtering request.
    """
    query: str = Field(..., description="Target search query")
    chunks: List[Dict[str, Any]] = Field(..., description="List of chunk dictionaries to compress")
    min_score_threshold: float = Field(default=0.0, description="Minimum relevance score threshold for filtering")
    max_tokens: int = Field(default=500, ge=50, le=4000, description="Maximum total compressed token budget")


class CompressedChunkItem(BaseModel):
    """
    Schema for an individual compressed text chunk.
    """
    chunk_id: Optional[str] = None
    original_text: str
    compressed_text: str
    relevance_score: float
    token_reduction_ratio: float = Field(..., description="Percentage of tokens saved during compression")


class CompressionResponse(BaseModel):
    """
    Schema for compression endpoint response.
    """
    status: str
    query: str
    original_chunk_count: int
    compressed_chunk_count: int
    compressed_chunks: List[CompressedChunkItem]