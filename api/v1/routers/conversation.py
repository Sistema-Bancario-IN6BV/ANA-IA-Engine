from __future__ import annotations

from fastapi import APIRouter, Depends

from api.v1.dependencies import get_conversation_service
from modules.conversation.schemas import ChatRequest, ChatResponse
from modules.conversation.service import ConversationService

router = APIRouter(tags=["conversation"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ChatResponse:
    """Analyzes user text and returns an empathic response.

    Called by ANA-Backend (ana.service.js) for real-time conversation
    with elderly users. Maintains backward compatibility with the original
    POST /chat contract.
    """
    return service.chat(
        text=request.text,
        user_name=request.user_name,
        user_age=request.user_age,
    )
