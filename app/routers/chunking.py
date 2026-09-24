from fastapi import APIRouter, HTTPException, status
from app.schemas.chunk import ChunkingRequest, ChunkingResponse, ChunkItem
from app.services.chunking_engine import ChunkingEngine

router = APIRouter(prefix="/api/v1/chunking", tags=["Chunking"])


@router.post("/process", response_model=ChunkingResponse)
async def process_text_chunking(request: ChunkingRequest):
    """
    Split provided raw text into chunks based on specified chunk_size and chunk_overlap parameters.
    """
    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty."
        )

    try:
        metadata = {"filename": request.filename}
        chunks_data = ChunkingEngine.recursive_character_chunking(
            text=request.text,
            metadata=metadata,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        chunks = [ChunkItem(**c) for c in chunks_data]
        
        return ChunkingResponse(
            status="success",
            total_chunks=len(chunks),
            chunks=chunks
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chunk document: {str(e)}"
        )