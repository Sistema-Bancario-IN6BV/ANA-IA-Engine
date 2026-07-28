from __future__ import annotations

import io
import logging

import PIL.Image
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from api.v1.dependencies import get_scene_analyzer
from core.exceptions import VisionInferenceError
from modules.vision.scene_analyzer import SceneAnalyzer
from modules.vision.schemas import SceneAnalysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vision", tags=["vision"])

_ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/tiff", "image/bmp", "image/gif"}
)


@router.post("/detect", response_model=SceneAnalysis)
async def detect_objects(
    file: UploadFile = File(...),
    analyzer: SceneAnalyzer = Depends(get_scene_analyzer),
) -> SceneAnalysis:
    """Detects objects in an image and returns an elderly-context scene analysis.

    Identifies: whether a person is present/alone, medication-adjacent objects
    (bottles, cups), and objects left on the floor that could be a trip hazard.

    Accepts: image/jpeg, image/png, image/tiff, image/bmp.
    """
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de imagen no soportado: {file.content_type}",
        )
    content = await file.read()
    try:
        image = PIL.Image.open(io.BytesIO(content)).convert("RGB")
        return analyzer.analyze_scene(image)
    except VisionInferenceError as exc:
        logger.error("Vision inference error: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message
        )
    except Exception as exc:
        logger.exception("Unexpected vision error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
