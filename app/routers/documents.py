from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from app.services.document_parser import DocumentParser

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


class DocumentUploadResponse(BaseModel):
    """
    Schema for document upload API response.
    """
    status: str
    metadata: Dict[str, Any]
    preview_text: str


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, TXT, or MD), parse its contents, and return metadata with a text preview.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Filename cannot be empty."
        )

    try:
        content = await file.read()
        extracted_text, metadata = DocumentParser.extract(file.filename, content)
        
        # Generate preview snippet (first 300 characters)
        preview = extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text
        
        return DocumentUploadResponse(
            status="success",
            metadata=metadata,
            preview_text=preview
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to process document: {str(e)}"
        )