-- Migration: Create documents table with vector support
-- Description: Initial schema for storing document chunks with embeddings
-- Requirements: 1.3, 5.2, 5.3

-- Enable the vector extension for pgvector support
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table with vector column for embeddings
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    embedding VECTOR(768), -- nomic-embed-text produces 768-dimensional vectors
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add constraints for data integrity
ALTER TABLE documents 
ADD CONSTRAINT documents_filename_not_empty CHECK (length(filename) > 0);

ALTER TABLE documents 
ADD CONSTRAINT documents_content_not_empty CHECK (length(content) > 0);

ALTER TABLE documents 
ADD CONSTRAINT documents_chunk_index_non_negative CHECK (chunk_index >= 0);

-- Create composite unique constraint to prevent duplicate chunks
ALTER TABLE documents 
ADD CONSTRAINT documents_unique_chunk UNIQUE (content_hash, chunk_index);