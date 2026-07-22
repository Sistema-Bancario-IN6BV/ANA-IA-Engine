from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core.config import settings
from core.exceptions import OCRProcessingError

if TYPE_CHECKING:
    import PIL.Image

logger = logging.getLogger(__name__)

# Real-world documents are usually photographed with a phone (uneven lighting,
# low effective resolution) rather than scanned — upscale small images and
# boost contrast before OCR to noticeably improve Tesseract's accuracy.
_MIN_DIMENSION_PX = 1500


def _preprocess(image: "PIL.Image.Image") -> "PIL.Image.Image":
    from PIL import Image, ImageOps

    grayscale = ImageOps.grayscale(image)
    contrasted = ImageOps.autocontrast(grayscale)

    width, height = contrasted.size
    smallest_side = min(width, height)
    if smallest_side and smallest_side < _MIN_DIMENSION_PX:
        scale = _MIN_DIMENSION_PX / smallest_side
        contrasted = contrasted.resize((round(width * scale), round(height * scale)), Image.LANCZOS)

    return contrasted


class OCRProcessor:
    """Extracts text from images and PDFs using Tesseract OCR.

    Args:
        lang: Tesseract language code (default: settings.ocr_language = "spa").
    """

    def __init__(self, lang: str | None = None) -> None:
        self._lang = lang or settings.ocr_language

    def extract_from_image(self, image: "PIL.Image.Image") -> str:
        """Extracts text from a PIL image.

        Args:
            image: Image to process.

        Returns:
            Extracted text as a string.

        Raises:
            OCRProcessingError: If Tesseract is unavailable or fails.
        """
        try:
            import pytesseract
            if settings.ocr_tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = settings.ocr_tesseract_cmd

            processed = _preprocess(image)
            try:
                return pytesseract.image_to_string(processed, lang=self._lang)
            except pytesseract.TesseractError:
                # Fallback to English if configured language pack is not installed
                return pytesseract.image_to_string(processed, lang="eng")
        except ImportError as exc:
            raise OCRProcessingError(
                "pytesseract is not installed. Run: pip install pytesseract"
            ) from exc
        except OCRProcessingError:
            raise
        except Exception as exc:
            raise OCRProcessingError(f"OCR failed: {exc}") from exc

    def extract_from_pdf(self, pdf_bytes: bytes) -> tuple[str, int]:
        """Extracts text from a PDF by converting each page to an image first.

        Args:
            pdf_bytes: Binary content of the PDF file.

        Returns:
            Tuple of (extracted_text, page_count).

        Raises:
            OCRProcessingError: If pdf2image or Tesseract are unavailable or fail.
        """
        try:
            from pdf2image import convert_from_bytes
        except ImportError as exc:
            raise OCRProcessingError(
                "pdf2image is not installed. Run: pip install pdf2image"
            ) from exc
        try:
            images = convert_from_bytes(pdf_bytes)
            text = "\n\n".join(self.extract_from_image(img) for img in images)
            return text, len(images)
        except OCRProcessingError:
            raise
        except Exception as exc:
            raise OCRProcessingError(f"PDF extraction failed: {exc}") from exc
