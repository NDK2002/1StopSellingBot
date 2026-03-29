"""RAG document management API routes."""

from fastapi import APIRouter, HTTPException

from app.config import get_supabase_client
from app.models.schemas import RAGDocumentCreate, RAGDocumentResponse, RAGDocumentUpdate
from app.services.rag import index_document

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/upload", response_model=RAGDocumentResponse)
async def upload_rag_document(doc: RAGDocumentCreate):
    """Upload a new RAG document and index it."""
    supabase = get_supabase_client()

    # Create document record
    result = supabase.table("rag_documents").insert({
        "title": doc.title,
        "content": doc.content,
        "doc_type": doc.doc_type,
        "metadata": doc.metadata,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to create document")

    document = result.data[0]

    # Index the document (chunk + embed)
    chunk_count = await index_document(document["id"], doc.content)

    return {**document, "_chunks_created": chunk_count}


@router.put("/{document_id}", response_model=RAGDocumentResponse)
async def update_rag_document(document_id: str, doc: RAGDocumentUpdate):
    """Update a RAG document."""
    supabase = get_supabase_client()
    data = doc.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase.table("rag_documents").update(data).eq("id", document_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    return result.data[0]


@router.post("/{document_id}/reindex")
async def reindex_rag_document(document_id: str):
    """Re-chunk and re-embed a RAG document."""
    supabase = get_supabase_client()

    result = supabase.table("rag_documents").select("*").eq("id", document_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    document = result.data[0]
    if not document.get("content"):
        raise HTTPException(status_code=400, detail="Document has no content to index")

    chunk_count = await index_document(document_id, document["content"])
    return {"message": "Document reindexed", "document_id": document_id, "chunks": chunk_count}


@router.get("/documents", response_model=list[RAGDocumentResponse])
async def list_rag_documents():
    """List all RAG documents."""
    supabase = get_supabase_client()
    result = supabase.table("rag_documents").select("*").order("created_at", desc=True).execute()
    return result.data or []


@router.delete("/{document_id}")
async def delete_rag_document(document_id: str):
    """Delete a RAG document and its chunks."""
    supabase = get_supabase_client()
    result = supabase.table("rag_documents").delete().eq("id", document_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted", "id": document_id}
