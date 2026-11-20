import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.user import User, RoleEnum
from app.models.profile import Student
from app.models.rag import Document, DocumentChunk
from app.rag.embedder import generate_embedding
from app.rag.guardrails import sanitize_retrieved_chunk

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2:
        return 0.0
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def search_documents(
    db: Session,
    query: str,
    user: Optional[User] = None,
    department_id: Optional[int] = None,
    semester: Optional[int] = None,
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Retrieves most semantically relevant document chunks for an academic query.
    Enforces authorization boundaries so students only see documents appropriate to their department/semester.
    """
    if not query.strip():
        return []

    query_vec = generate_embedding(query)

    # Resolve authorization filters for students
    allowed_dept_id = department_id
    allowed_semester = semester
    if user and user.role == RoleEnum.STUDENT:
        student = db.query(Student).filter(Student.user_id == user.id).first()
        if student:
            allowed_dept_id = student.department_id
            allowed_semester = student.current_semester

    # Build base query
    q = db.query(DocumentChunk, Document).join(Document, DocumentChunk.document_id == Document.id)
    if allowed_dept_id:
        q = q.filter((Document.department_id == allowed_dept_id) | (Document.department_id == None))
    if allowed_semester:
        q = q.filter((Document.semester == allowed_semester) | (Document.semester == None))

    records = q.all()
    if not records:
        return []

    # Score chunks
    scored_results = []
    for chunk, doc in records:
        chunk_embedding = chunk.embedding
        if not chunk_embedding:
            continue
        sim = cosine_similarity(query_vec, chunk_embedding)
        clean_content = sanitize_retrieved_chunk(chunk.content)
        scored_results.append({
            "chunk_id": chunk.id,
            "document_id": doc.id,
            "document_title": doc.title,
            "page_number": chunk.page_number,
            "content": clean_content,
            "score": round(sim, 4)
        })

    # Sort by descending similarity score
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]
