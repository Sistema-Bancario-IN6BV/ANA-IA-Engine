from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client():
    """Lazily instantiates the HuggingFace InferenceClient (singleton)."""
    try:
        from huggingface_hub import InferenceClient
        return InferenceClient(token=settings.huggingface_api_key)
    except ImportError:
        logger.warning("huggingface_hub not installed; HF remote inference unavailable")
        return None


class HFClient:
    """Thin wrapper over HuggingFace InferenceClient.

    Used when models are served remotely on HF rather than loaded locally.
    """

    def infer(self, model: str, inputs: Any, **kwargs: Any) -> Any:
        """Runs inference on a HuggingFace hosted model.

        Args:
            model: HF model ID (e.g. "facebook/detr-resnet-50").
            inputs: Input payload (text, image bytes, etc.).
            **kwargs: Additional parameters forwarded to the API.

        Returns:
            API response payload.

        Raises:
            RuntimeError: If the HF client is not available.
        """
        client = _get_client()
        if client is None:
            raise RuntimeError("HuggingFace InferenceClient is not available")
        return client.post(json={"inputs": inputs, **kwargs}, model=model)
