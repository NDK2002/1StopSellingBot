-- Search RAG chunks by vector similarity
CREATE OR REPLACE FUNCTION search_rag_chunks(
    query_embedding vector(768),
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    chunk_index int,
    content text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        rc.id,
        rc.document_id,
        rc.chunk_index,
        rc.content,
        1 - (rc.embedding <=> query_embedding) AS similarity
    FROM rag_chunks rc
    WHERE rc.embedding IS NOT NULL
    ORDER BY rc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Search product embeddings by vector similarity
CREATE OR REPLACE FUNCTION search_product_embeddings(
    query_embedding vector(768),
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    product_id uuid,
    content text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        pe.id,
        pe.product_id,
        pe.content,
        1 - (pe.embedding <=> query_embedding) AS similarity
    FROM product_embeddings pe
    WHERE pe.embedding IS NOT NULL
    ORDER BY pe.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
