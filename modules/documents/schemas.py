from __future__ import annotations

from pydantic import BaseModel


class DocumentReadResult(BaseModel):
    text: str
    pages: int
    entities: list[str]
    summary: str
