from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging import CorrelationIdMiddleware, setup_logging
from api.v1.routers import conversation, documents, emotion, vision, voice


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(debug=settings.debug)
    yield


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.app_name,
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root + health — ANA-Backend calls GET /health, keep at root
    @app.get("/", tags=["meta"])
    def root() -> dict:
        return {
            "status": "ANA NLP API running",
            "version": "2.0.0",
            "endpoints": {
                "chat": "POST /chat",
                "analyze": "POST /analyze",
                "vision": "POST /api/v1/vision/detect",
                "documents": "POST /api/v1/documents/read",
                "health": "GET /health",
            },
        }

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "healthy", "service": "ANA"}

    # Existing endpoints at their original paths (backward compat with ANA-Backend)
    app.include_router(conversation.router)  # POST /chat
    app.include_router(emotion.router)       # POST /analyze
    app.include_router(voice.router)         # POST /voice-chat, POST /voice-chat/speak

    # New endpoints under /api/v1
    app.include_router(vision.router, prefix="/api/v1")     # POST /api/v1/vision/detect
    app.include_router(documents.router, prefix="/api/v1")  # POST /api/v1/documents/read

    return app


app = create_app()
