from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from api.v1.dependencies import get_doc_reader
from core.exceptions import DocumentReadError, OCRProcessingError
from modules.documents.doc_reader import DocReader
from modules.documents.schemas import DocumentReadResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

_ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/tiff",
        "image/bmp",
    }
)
_MAX_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB


@router.post("/read", response_model=DocumentReadResult)
async def read_document(
    file: UploadFile = File(...),
    reader: DocReader = Depends(get_doc_reader),
) -> DocumentReadResult:
    """Extracts text and health entities from a PDF or image document.

    Useful for reading prescriptions, medical reports, or appointment letters.
    Entity detection identifies: medications, diagnoses, dates, doctors, hospitals.

    Accepts: PDF, PNG, JPG, TIFF, BMP. Max size: 10 MB.
    """
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de archivo no soportado: {file.content_type}",
        )
    content = await file.read()
    if len(content) > _MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo excede el límite de 10 MB",
        )
    try:
        return reader.read(content, file.filename or "document")
    except (DocumentReadError, OCRProcessingError) as exc:
        logger.error("Document read error: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message
        )
    except Exception as exc:
        logger.exception("Unexpected document error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
