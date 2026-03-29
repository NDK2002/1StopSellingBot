"""RAG service: chunking, embedding, and retrieval."""

import re

from app.config import get_supabase_client
from app.services.embedding import create_embedding, create_embeddings_batch


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep overlap
            words = current_chunk.split()
            overlap_text = " ".join(words[-overlap:]) if len(words) > overlap else ""
            current_chunk = overlap_text + " " + sentence
        else:
            current_chunk += " " + sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]


async def index_document(document_id: str, content: str) -> int:
    """Chunk and embed a document, storing chunks in rag_chunks."""
    supabase = get_supabase_client()

    # Delete existing chunks for this document
    supabase.table("rag_chunks").delete().eq("document_id", document_id).execute()

    # Chunk the content
    chunks = chunk_text(content)

    # Create embeddings for all chunks
    embeddings = await create_embeddings_batch(chunks)

    # Insert chunks with embeddings
    rows = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        rows.append({
            "document_id": document_id,
            "chunk_index": i,
            "content": chunk,
            "embedding": embedding,
        })

    if rows:
        supabase.table("rag_chunks").insert(rows).execute()

    return len(rows)


async def search_rag(query: str, top_k: int = 5) -> list[dict]:
    """Search RAG chunks by semantic similarity."""
    supabase = get_supabase_client()
    query_embedding = await create_embedding(query)

    # Use Supabase RPC for vector similarity search
    result = supabase.rpc(
        "search_rag_chunks",
        {"query_embedding": query_embedding, "match_count": top_k},
    ).execute()

    return result.data if result.data else []


async def search_products(query: str, top_k: int = 5) -> list[dict]:
    """Search product embeddings by semantic similarity."""
    supabase = get_supabase_client()
    query_embedding = await create_embedding(query)

    result = supabase.rpc(
        "search_product_embeddings",
        {"query_embedding": query_embedding, "match_count": top_k},
    ).execute()

    return result.data if result.data else []
