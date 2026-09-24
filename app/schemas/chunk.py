from pydantic import BaseModel, Field
from typing import Dict, Any, List


class ChunkItem(BaseModel):
    """
    Schema representing an individual text chunk with metadata.
    """
    chunk_id: str = Field(..., description="Unique UUID for the chunk")
    text: str = Field(..., description="The actual text content of the chunk")
    index: int = Field(..., description="Sequential position index in the document")
    token_count: int = Field(..., description="Calculated token length")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Associated document metadata")


class ChunkingRequest(BaseModel):
    """
    Schema for requesting document text chunking.
    """
    text: str = Field(..., description="Raw input text to be split")
    filename: str = Field(default="untitled.txt", description="Source document filename")
    chunk_size: int = Field(default=500, ge=100, le=2000, description="Target character size per chunk")
    chunk_overlap: int = Field(default=50, ge=0, le=500, description="Overlap size between adjacent chunks")


class ChunkingResponse(BaseModel):
    """
    Schema for chunking operation response.
    """
    status: str
    total_chunks: int
    chunks: List[ChunkItem]