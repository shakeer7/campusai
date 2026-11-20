from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ToolCallInfo(BaseModel):
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[Any] = None
    status: str = "success"  # "success" or "failed"
    execution_time_ms: Optional[float] = None


class CitationInfo(BaseModel):
    document_title: str
    page_number: int
    snippet: str
    similarity_score: Optional[float] = None


class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system", "tool"
    content: str
    name: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    preferred_language: Optional[str] = None  # en, te, hi, te-Latn (Romanized Telugu)
    stream: bool = False
    voice_output: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    detected_language: str
    language_confidence: float = 0.95
    tools_executed: List[ToolCallInfo] = Field(default_factory=list)
    citations: List[CitationInfo] = Field(default_factory=list)
    workflow_state: Optional[Dict[str, Any]] = None
    audio_base64: Optional[str] = None


class VoiceProcessRequest(BaseModel):
    audio_base64: str
    conversation_id: Optional[str] = None
    audio_format: str = "webm"  # webm, wav, mp3
