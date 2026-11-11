from fastapi import APIRouter, HTTPException, status
from app.schemas.compression import CompressionRequest, CompressionResponse, CompressedChunkItem
from app.services.context_compressor import ContextCompressorService

router = APIRouter(prefix="/api/v1/search/compress", tags=["Context Compression"])


@router.post("/filter", response_model=CompressionResponse)
async def compress_context_chunks(request: CompressionRequest):
    """
    Filter low-scoring candidate chunks and compress text at sentence level to reduce token overhead.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    if not request.chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chunks list cannot be empty."
        )

    try:
        compressor = ContextCompressorService()
        compressed_list = compressor.process_compression(
            query=request.query,
            chunks=request.chunks,
            min_score_threshold=request.min_score_threshold,
            max_tokens=request.max_tokens
        )

        results = [CompressedChunkItem(**item) for item in compressed_list]

        return CompressionResponse(
            status="success",
            query=request.query,
            original_chunk_count=len(request.chunks),
            compressed_chunk_count=len(results),
            compressed_chunks=results
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context compression failed: {str(e)}"
        )