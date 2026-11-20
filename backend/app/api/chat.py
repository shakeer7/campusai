import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.ai.bedrock_client import run_bedrock_orchestration
from app.ai.translator import translate_with_aws
from pydantic import BaseModel
from typing import Optional

class TranslateRequest(BaseModel):
    text: str
    target_language: str
    source_language: Optional[str] = "auto"

class TranslateResponse(BaseModel):
    translated_text: str
    target_language: str
    source_language: str
    service: str = "AWS Translate"

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["AI Chat & Bedrock"])


@router.post("", response_model=ChatResponse)
def chat_with_campusai(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        conv_id = req.conversation_id or f"conv-{current_user.id}"
        result = run_bedrock_orchestration(
            user_message=req.message,
            conversation_history=[],
            current_user=current_user,
            db=db,
            preferred_language=req.preferred_language
        )
        return ChatResponse(
            conversation_id=conv_id,
            message=result["message"],
            detected_language=result["detected_language"],
            language_confidence=result["language_confidence"],
            tools_executed=result["tools_executed"],
            citations=result["citations"]
        )
    except Exception as e:
        logger.error(f"Chat execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI chat error: {str(e)}")


@router.get("/stream")
def stream_chat(
    message: str = Query(...),
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Server-Sent Events (SSE) streaming chat endpoint."""
    from app.auth.security import decode_token
    try:
        payload = decode_token(token)
        user = db.query(User).filter(User.id == payload.get("user_id")).first()
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    def event_generator():
        result = run_bedrock_orchestration(
            user_message=message,
            conversation_history=[],
            current_user=user,
            db=db
        )
        # Yield tool notifications first if any
        for tool in result.get("tools_executed", []):
            yield f"data: {json.dumps({'type': 'tool', 'tool_name': tool['tool_name'], 'status': tool['status']})}\n\n"

        # Stream words/tokens
        full_text = result.get("message", "")
        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'type': 'content', 'delta': chunk})}\n\n"

        # Yield citations
        if result.get("citations"):
            yield f"data: {json.dumps({'type': 'citations', 'citations': result['citations']})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/translate", response_model=TranslateResponse)
def translate_message_endpoint(
    req: TranslateRequest,
    current_user: User = Depends(get_current_user)
):
    """Neural translation endpoint powered by AWS Translate."""
    try:
        translated_text, target_lang = translate_with_aws(
            text=req.text,
            target_lang=req.target_language,
            source_lang=req.source_language or "auto"
        )
        return TranslateResponse(
            translated_text=translated_text,
            target_language=target_lang,
            source_language=req.source_language or "auto",
            service="AWS Translate"
        )
    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

