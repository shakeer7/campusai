import os
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, RoleEnum
from app.models.rag import Document, DocumentChunk, DocumentTypeEnum
from app.auth.dependencies import get_current_user, require_roles
from app.schemas.rag import DocumentUploadResponse, DocumentSearchRequest, DocumentChunkResult
from app.rag.parser import extract_text_by_pages
from app.rag.chunker import split_text_into_chunks
from app.rag.embedder import generate_embedding
from app.rag.retriever import search_documents

router = APIRouter(prefix="/rag", tags=["Academic RAG"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_academic_document(
    title: str = Form(...),
    doc_type: DocumentTypeEnum = Form(DocumentTypeEnum.SYLLABUS),
    department_id: Optional[int] = Form(None),
    semester: Optional[int] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([RoleEnum.FACULTY, RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    pages_data = extract_text_by_pages(content)
    if not pages_data:
        raise HTTPException(
            status_code=422,
            detail="No readable text could be extracted from the PDF. Document may contain only raster images."
        )

    chunks = split_text_into_chunks(pages_data, chunk_size=500, chunk_overlap=50)

    # Save Document record
    doc = Document(
        title=title,
        doc_type=doc_type,
        department_id=department_id,
        semester=semester,
        file_size_bytes=len(content),
        mime_type="application/pdf",
        uploaded_by=current_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Save chunks with embeddings
    for chunk in chunks:
        vec = generate_embedding(chunk["content"])
        db_chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=chunk["chunk_index"],
            content=chunk["content"],
            page_number=chunk["page_number"],
            token_count=chunk["token_count"],
            embedding=vec
        )
        db.add(db_chunk)

    db.commit()

    return DocumentUploadResponse(
        document_id=doc.id,
        title=doc.title,
        total_chunks=len(chunks),
        message=f"Document successfully parsed and indexed into {len(chunks)} searchable chunks."
    )


@router.post("/search", response_model=List[DocumentChunkResult])
def search_academic_documents_endpoint(
    req: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = search_documents(
        db=db,
        query=req.query,
        user=current_user,
        department_id=req.department_id,
        semester=req.semester,
        top_k=req.top_k
    )
    return [
        DocumentChunkResult(
            chunk_id=r["chunk_id"],
            document_id=r["document_id"],
            document_title=r["document_title"],
            page_number=r["page_number"],
            content=r["content"],
            score=r["score"]
        )
        for r in results
    ]
