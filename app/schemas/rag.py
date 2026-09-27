from pydantic import BaseModel, Field
from typing import List, Optional


class RAGQueryRequest(BaseModel):
    """
    Schema for RAG chat stream request.
    """
    query: str = Field(..., description="User question or query")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of context chunks to retrieve")
    filename_filter: Optional[str] = Field(default=None, description="Optional filename filter")


class CitationItem(BaseModel):
    """
    Schema representing source document citations used in the answer.
    """
    chunk_id: str
    filename: str
    score: float
    text_snippet: str