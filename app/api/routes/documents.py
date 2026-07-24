import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from pydantic import BaseModel, Field
from app.services.ingest_service import ingest_file_to_faiss
from app.core.security import get_current_admin


router = APIRouter()

class DocumentUploadResponse(BaseModel):
    filename: str = Field(..., description="Uploaded document filename")
    status: str = Field(..., description="Ingestion processing status")
    chunks_added: int = Field(..., description="Number of text chunks added to FAISS index")
    message: str = Field(..., description="Details or success message")

@router.post("/documents/upload", response_model=DocumentUploadResponse, summary="Upload a document and index its chunks into FAISS")
async def upload_document(file: UploadFile = File(...), current_user: str = Depends(get_current_admin)):

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty."
        )

    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".txt", ".pdf", ".docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{suffix}'. Supported formats are: .pdf, .docx, .txt"
        )

    # Save uploaded file to a temporary file for processing
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            shutil.copyfileobj(file.file, temp_file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving uploaded file: {str(e)}"
        )
    finally:
        await file.close()

    try:
        result = ingest_file_to_faiss(file_path=str(temp_path))
        return DocumentUploadResponse(
            filename=file.filename,
            status="success",
            chunks_added=result.get("chunks_added", 0),
            message=f"Successfully ingested '{file.filename}' and updated FAISS vector store."
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running ingestion pipeline: {str(e)}"
        )
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
