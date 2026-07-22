from __future__ import annotations


class ANABaseException(Exception):
    """Base class for all ANA domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AnalysisError(ANABaseException):
    """Raised when the NLP analysis pipeline fails."""


class LLMServiceError(ANABaseException):
    """Raised when LLM (Groq) response generation fails."""


class VisionInferenceError(ANABaseException):
    """Raised when object-detection inference fails."""


class OCRProcessingError(ANABaseException):
    """Raised when OCR text extraction fails."""


class DocumentReadError(ANABaseException):
    """Raised when document comprehension or file parsing fails."""
