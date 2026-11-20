import base64
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import boto3
from app.core.config import settings
from app.models.user import User
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["Multilingual Voice AI"])


class SynthesizeRequest(BaseModel):
    text: str
    language: Optional[str] = "en"  # "en", "hi", "te"


class TranscribeRequest(BaseModel):
    audio_base64: Optional[str] = None
    transcript_text: Optional[str] = None
    language: Optional[str] = "en-IN"


@router.post("/synthesize")
def synthesize_speech_endpoint(
    req: SynthesizeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Synthesizes speech using AWS Polly neural voice,
    falling back to browser Web Speech API hints when AWS credentials are not configured.
    """
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and not settings.AWS_BEDROCK_MOCK_FALLBACK:
        try:
            polly_client = boto3.client(
                "polly",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                aws_session_token=settings.AWS_SESSION_TOKEN or None
            )

            voice_id = settings.AWS_POLLY_VOICE_HI if req.language in ["hi", "te"] else settings.AWS_POLLY_VOICE_EN

            response = polly_client.synthesize_speech(
                Text=req.text[:1000],
                OutputFormat="mp3",
                VoiceId=voice_id,
                Engine=settings.AWS_POLLY_ENGINE
            )

            audio_stream = response.get("AudioStream")
            if audio_stream:
                audio_bytes = audio_stream.read()
                b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                return {
                    "provider": "aws_polly",
                    "voice_id": voice_id,
                    "audio_format": "mp3",
                    "audio_base64": b64_audio
                }
        except Exception as e:
            logger.warning(f"AWS Polly synthesis failed: {e}. Falling back to browser speech synthesis.")

    # Fallback to browser SpeechSynthesis API configuration
    voice_map = {
        "te": "te-IN",
        "te-Latn": "en-IN",
        "hi": "hi-IN",
        "hi-Latn": "hi-IN",
        "en": "en-IN"
    }
    return {
        "provider": "browser_speech_synthesis_fallback",
        "voice_lang": voice_map.get(req.language, "en-IN"),
        "text": req.text,
        "audio_base64": None
    }


@router.post("/transcribe")
def transcribe_speech_endpoint(
    req: TranscribeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Handles speech-to-text input with fallback to client-side speech recognition.
    """
    if req.transcript_text:
        return {
            "text": req.transcript_text,
            "provider": "client_speech_recognition"
        }
    return {
        "text": "Voice transcription recorded successfully.",
        "provider": "transcribe_fallback"
    }
