# Supabase Setup Guide for Live Testing

This guide will help you set up your Supabase database for live integration testing.

## Current Issue

The live tests are failing because:
1. You're using the **anonymous key** which has Row Level Security (RLS) restrictions
2. For testing, you need the **service role key** which bypasses RLS
3. The database table may not exist yet

## Step 1: Get Your Service Role Key

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project: `tmbotmpvcrbbqvezzrui`
3. Go to **Settings** → **API**
4. Copy the **service_role** key (not the anon key)
5. Update your `.env` file:

```bash
# Replace SUPABASE_KEY with SUPABASE_SERVICE_KEY
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

## Step 2: Create the Database Table

You need to run the migration scripts to create the table structure.

### Option A: Using Supabase Dashboard (Recommended)

1. Go to **SQL Editor** in your Supabase dashboard
2. Run each migration file in order:

**Migration 1 - Create Table:**
```sql
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
```

**Migration 2 - Create Indexes:**
```sql
-- Create vector similarity search index using ivfflat
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
```

**Migration 3 - Create Functions:**
```sql
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
```

### Option B: Using Supabase CLI (Advanced)

If you have the Supabase CLI installed:

```bash
# Initialize Supabase in your project
supabase init

# Link to your remote project
supabase link --project-ref tmbotmpvcrbbqvezzrui

# Run migrations
supabase db push
```

## Step 3: Update Environment Configuration

Update your `.env` file to use the service role key:

```bash
# Supabase Configuration
SUPABASE_URL=https://tmbotmpvcrbbqvezzrui.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here  # Use service role key for testing
SUPABASE_TABLE_NAME=documents
SUPABASE_TIMEOUT=30
SUPABASE_MAX_RETRIES=3
```

## Step 4: Test the Setup

Once you've completed the above steps, test the connection:

```bash
# Test database connection
python run_live_tests.py health

# Test basic operations
python run_live_tests.py basic

# Explore database contents
python run_live_tests.py explore
```

## Step 5: Security Considerations

**Important:** The service role key bypasses all security policies and should only be used for:
- Testing and development
- Server-side operations
- Administrative tasks

**Never expose the service role key in:**
- Client-side code
- Public repositories
- Production applications accessible to users

For production applications, use the anonymous key with proper RLS policies.

## Troubleshooting

### Error: "extension vector does not exist"
- Your Supabase project doesn't have the pgvector extension enabled
- Contact Supabase support or enable it in the dashboard under Database → Extensions

### Error: "relation documents does not exist"
- The table hasn't been created yet
- Run the migration scripts from Step 2

### Error: "row-level security policy"
- You're still using the anonymous key instead of the service role key
- Update your `.env` file with the service role key

### Error: "permission denied"
- The service role key is incorrect
- Double-check you copied the right key from the Supabase dashboard

## Next Steps

Once the setup is complete, you can:

1. **Run live tests** to validate your Supabase integration
2. **Create sample documents** for manual exploration
3. **Test vector similarity search** with real data
4. **Explore the database** through the Supabase dashboard

The live tests will create real data in your database, allowing you to:
- Verify vector embeddings are stored correctly
- Test similarity search functionality
- Explore data structure in the Supabase dashboard
- Validate performance with realistic data volumes