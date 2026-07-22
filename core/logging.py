from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Returns the correlation ID for the current request context."""
    return _correlation_id.get()


def setup_logging(debug: bool = False) -> None:
    """Configures root logger with a JSON-friendly format."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format=(
            '{"time": "%(asctime)s", "level": "%(levelname)s", '
            '"name": "%(name)s", "msg": "%(message)s"}'
        ),
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Attaches a UUID correlation_id to every request for distributed tracing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        token = _correlation_id.set(correlation_id)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            _correlation_id.reset(token)
