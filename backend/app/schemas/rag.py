from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.rag import DocumentTypeEnum


class DocumentMetadata(BaseModel):
    id: int
    title: str
    doc_type: DocumentTypeEnum
    department_code: Optional[str] = None
    semester: Optional[int] = None
    file_size_bytes: int
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document_id: int
    title: str
    total_chunks: int
    message: str


class DocumentSearchRequest(BaseModel):
    query: str
    department_id: Optional[int] = None
    semester: Optional[int] = None
    top_k: int = 4


class DocumentChunkResult(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    page_number: int
    content: str
    score: float
