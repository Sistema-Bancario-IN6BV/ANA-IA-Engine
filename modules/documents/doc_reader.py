from __future__ import annotations

import io
import logging
import re
from pathlib import Path

import PIL.Image

from core.exceptions import DocumentReadError
from modules.documents.ocr import OCRProcessor
from modules.documents.schemas import DocumentReadResult

logger = logging.getLogger(__name__)

_HEALTH_KEYWORDS: list[str] = [
    "pastilla", "medicamento", "medicina", "dosis", "tableta",
    "diagnóstico", "diagnostico", "cita", "consulta",
    "fecha", "hospital", "clínica", "clinica", "doctor", "médico", "medico",
    "receta", "tratamiento", "cirugía", "cirugia", "análisis", "analisis",
    "presión", "presion", "glucosa", "diabetes", "corazón", "corazon",
]

# Structured patterns that pull out actual values (a date, a name, a dose)
# instead of just flagging that a generic category keyword appears somewhere.
_DATE_PATTERN = re.compile(r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b")
_DOCTOR_PATTERN = re.compile(
    r"\b(?:Dr|Dra)\.?\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]+){0,2}"
)
_HOSPITAL_PATTERN = re.compile(
    r"\b(?:Hospital|Cl[ií]nica|Centro M[ée]dico)\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]*"
    r"(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]*){0,3}"
)
_MEDICATION_DOSE_PATTERN = re.compile(
    r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+\d+(?:[.,]\d+)?\s?(?:mg|ml|mcg|g|UI)\b"
)

_ALLOWED_SUFFIXES: frozenset[str] = frozenset(
    {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}
)


class DocReader:
    """Reads health-related documents (PDF or images) and extracts key entities.

    Primary extraction: OCR (Tesseract). Entity detection: regex patterns for
    dates, doctor names, hospital/clinic names, and medication+dosage, plus a
    fallback list of generic health-related keyword hits.

    Covers H5 (secure document storage context) and H4 (health data extraction).
    """

    def __init__(self) -> None:
        self._ocr = OCRProcessor()

    def read(self, content: bytes, filename: str) -> DocumentReadResult:
        """Reads a document and returns structured text and health entities.

        Args:
            content: Raw bytes of the uploaded file.
            filename: Original filename used to determine file type.

        Returns:
            DocumentReadResult with text, page count, entities, and summary.

        Raises:
            DocumentReadError: If the file type is unsupported or extraction fails.
        """
        suffix = Path(filename).suffix.lower()
        if suffix not in _ALLOWED_SUFFIXES:
            raise DocumentReadError(
                f"Tipo de archivo no soportado: {suffix}. "
                f"Use: {', '.join(sorted(_ALLOWED_SUFFIXES))}"
            )
        try:
            if suffix == ".pdf":
                text, pages = self._ocr.extract_from_pdf(content)
            else:
                image = PIL.Image.open(io.BytesIO(content))
                text = self._ocr.extract_from_image(image)
                pages = 1
        except DocumentReadError:
            raise
        except Exception as exc:
            raise DocumentReadError(f"Error leyendo el documento: {exc}") from exc

        entities = self._extract_entities(text)
        summary = self._build_summary(text, entities)

        return DocumentReadResult(text=text, pages=pages, entities=entities, summary=summary)

    def _extract_entities(self, text: str) -> list[str]:
        entities: set[str] = set()
        entities.update(match.strip() for match in _DATE_PATTERN.findall(text))
        entities.update(match.strip() for match in _DOCTOR_PATTERN.findall(text))
        entities.update(match.strip() for match in _HOSPITAL_PATTERN.findall(text))
        entities.update(match.strip() for match in _MEDICATION_DOSE_PATTERN.findall(text))

        text_lower = text.lower()
        entities.update(kw for kw in _HEALTH_KEYWORDS if kw in text_lower)
        return sorted(entities)

    @staticmethod
    def _build_summary(text: str, entities: list[str]) -> str:
        word_count = len(text.split())
        if not entities:
            return f"Documento procesado ({word_count} palabras). No se detectaron entidades de salud específicas."
        return (
            f"Documento procesado ({word_count} palabras). "
            f"Entidades detectadas: {', '.join(entities)}."
        )
