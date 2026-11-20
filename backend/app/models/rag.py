import enum
import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, TypeDecorator
from sqlalchemy.orm import relationship
from app.core.database import Base

# Robust Vector type decorator that gracefully falls back to JSON text when pgvector is not installed
class SafeVectorType(TypeDecorator):
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 1536):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dim))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            if dialect.name == "postgresql":
                return value
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [float(x.strip()) for x in value.strip("[]").split(",") if x.strip()]
        return value


class DocumentTypeEnum(str, enum.Enum):
    SYLLABUS = "syllabus"
    REGULATION = "regulation"
    LECTURE_NOTES = "lecture_notes"
    CIRCULAR = "circular"
    POLICY = "policy"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    doc_type = Column(Enum(DocumentTypeEnum), default=DocumentTypeEnum.SYLLABUS, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    semester = Column(Integer, nullable=True)
    s3_key = Column(String(500), nullable=True)
    local_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    mime_type = Column(String(100), default="application/pdf", nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    embedding = Column(SafeVectorType(dim=1024), nullable=True)  # Bedrock Titan v2 default: 1024/1536
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="chunks")
