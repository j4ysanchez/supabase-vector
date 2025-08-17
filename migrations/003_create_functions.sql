-- Migration: Create utility functions and triggers
-- Description: Add helper functions for document management and automatic timestamp updates
-- Requirements: 1.3, 5.2, 5.3

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at on document changes
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate document statistics
CREATE OR REPLACE FUNCTION get_document_stats(doc_filename TEXT)
RETURNS TABLE (
    total_chunks INTEGER,
    total_characters INTEGER,
    has_embeddings BOOLEAN,
    first_created TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_chunks,
        SUM(LENGTH(content))::INTEGER as total_characters,
        BOOL_AND(embedding IS NOT NULL) as has_embeddings,
        MIN(created_at) as first_created,
        MAX(updated_at) as last_updated
    FROM documents 
    WHERE filename = doc_filename;
END;
$$ LANGUAGE plpgsql;

-- Function for similarity search with metadata filtering
CREATE OR REPLACE FUNCTION similarity_search(
    query_embedding VECTOR(768),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10,
    filename_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    filename TEXT,
    chunk_index INTEGER,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.filename,
        d.chunk_index,
        d.content,
        (1 - (d.embedding <=> query_embedding)) as similarity,
        d.metadata
    FROM documents d
    WHERE d.embedding IS NOT NULL
        AND (filename_filter IS NULL OR d.filename = filename_filter)
        AND (1 - (d.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY d.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;