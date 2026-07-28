from __future__ import annotations

from typing import Union

from pydantic import BaseModel


class ChatRequest(BaseModel):
    text: str
    user_name: str = ""
    user_age: int = 0


class ChatResponse(BaseModel):
    analysis: dict
    trend: str
    response: Union[dict, str]
    response_mode: str
