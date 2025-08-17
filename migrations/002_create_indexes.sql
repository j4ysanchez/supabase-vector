-- Migration: Create indexes for efficient querying and vector similarity search
-- Description: Add performance indexes for vector search and metadata lookups
-- Requirements: 1.3, 5.2, 5.3

-- Create vector similarity search index using ivfflat
-- This index enables efficient approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS documents_embedding_ivfflat_idx 
ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index on filename for efficient file-based lookups
CREATE INDEX IF NOT EXISTS documents_filename_idx 
ON documents (filename);

-- Create index on content_hash for duplicate detection
CREATE INDEX IF NOT EXISTS documents_content_hash_idx 
ON documents (content_hash);

-- Create composite index for file-based chunk retrieval
CREATE INDEX IF NOT EXISTS documents_filename_chunk_idx 
ON documents (filename, chunk_index);

-- Create index on created_at for temporal queries
CREATE INDEX IF NOT EXISTS documents_created_at_idx 
ON documents (created_at DESC);

-- Create partial index for documents with embeddings (for similarity search)
CREATE INDEX IF NOT EXISTS documents_embedding_exists_idx 
ON documents (id) 
WHERE embedding IS NOT NULL;