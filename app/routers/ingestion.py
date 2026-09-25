from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from app.services.document_parser import DocumentParser
from app.services.chunking_engine import ChunkingEngine
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion Pipeline"])


class IngestionResponse(BaseModel):
    """
    Schema for full document ingestion pipeline response.
    """
    status: str
    filename: str
    total_chunks_stored: int
    collection_name: str


@router.post("/document", response_model=IngestionResponse)
async def ingest_document(
    file: UploadFile = File(...),
    chunk_size: int = 500,
    chunk_overlap: int = 50
):
    """
    Full End-to-End Pipeline: Upload file -> Parse text -> Generate Chunks -> Compute Embeddings -> Store in Qdrant.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty."
        )

    try:
        content = await file.read()
        extracted_text, metadata = DocumentParser.extract(file.filename, content)

        chunks_data = ChunkingEngine.recursive_character_chunking(
            text=extracted_text,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        vector_service = VectorStoreService()
        stored_count = vector_service.upsert_chunks(chunks_data)

        return IngestionResponse(
            status="success",
            filename=file.filename,
            total_chunks_stored=stored_count,
            collection_name=vector_service.client.get_collection(
                collection_name="enterprise_rag_chunks"
            ).config.params.vectors.size and "enterprise_rag_chunks"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion pipeline failed: {str(e)}"
        )