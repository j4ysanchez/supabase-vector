# Database Migrations

This directory contains SQL migration scripts to set up the Supabase database schema for the Python CLI Vector DB application.

## Migration Files

1. **001_create_documents_table.sql** - Creates the main documents table with vector support
2. **002_create_indexes.sql** - Creates performance indexes including vector similarity search
3. **003_create_functions.sql** - Creates utility functions and triggers
4. **004_create_rls_policies.sql** - Sets up Row Level Security policies
5. **run_migrations.sql** - Master script to run all migrations in order
6. **verify_schema.sql** - Verification script to check the setup

## Prerequisites

- Supabase project with PostgreSQL database
- pgvector extension available (enabled automatically in migration 001)
- Database user with sufficient privileges to create tables, indexes, and functions

## Usage

### Option 1: Supabase Dashboard (Recommended)

1. Open your Supabase project dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of each migration file in order:
   - 001_create_documents_table.sql
   - 002_create_indexes.sql
   - 003_create_functions.sql
   - 004_create_rls_policies.sql
4. Execute each script
5. Run verify_schema.sql to confirm the setup

### Option 2: Command Line (psql)

```bash
# Connect to your Supabase database
psql "postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:5432/postgres"

# Run migrations in order
\i migrations/001_create_documents_table.sql
\i migrations/002_create_indexes.sql
\i migrations/003_create_functions.sql
\i migrations/004_create_rls_policies.sql

# Verify setup
\i migrations/verify_schema.sql
```

### Option 3: Single Script

```bash
# Run all migrations at once
psql "postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:5432/postgres" -f migrations/run_migrations.sql
```

## Schema Overview

### Documents Table

The main table stores document chunks with the following structure:

- `id` (UUID) - Primary key
- `filename` (TEXT) - Original filename
- `file_path` (TEXT) - Full path to source file
- `content_hash` (TEXT) - SHA-256 hash for duplicate detection
- `chunk_index` (INTEGER) - Position within the original document
- `content` (TEXT) - Text content of the chunk
- `embedding` (VECTOR(768)) - Vector representation from nomic-embed-text
- `metadata` (JSONB) - Additional information
- `created_at` (TIMESTAMP) - Creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp

### Indexes

- **Vector similarity search**: ivfflat index on embedding column
- **Filename lookup**: B-tree index on filename
- **Duplicate detection**: B-tree index on content_hash
- **Composite queries**: Multi-column indexes for common query patterns

### Functions

- `update_updated_at_column()` - Automatically updates timestamp on row changes
- `get_document_stats(filename)` - Returns statistics for a document
- `similarity_search(embedding, threshold, limit, filename_filter)` - Performs vector similarity search

### Security

Row Level Security (RLS) is enabled with policies allowing authenticated users to:
- Read all documents
- Insert new documents
- Update existing documents
- Delete documents

## Verification

After running the migrations, execute the verification script to ensure everything was set up correctly:

```sql
\i migrations/verify_schema.sql
```

This will check:
- Vector extension is enabled
- Documents table structure is correct
- All indexes were created
- Functions are available
- RLS policies are in place

## Troubleshooting

### Common Issues

1. **Vector extension not available**: Ensure your Supabase project supports pgvector
2. **Permission denied**: Check that your database user has CREATE privileges
3. **Index creation fails**: Verify the table exists before creating indexes
4. **RLS policies conflict**: Drop existing policies if re-running migrations

### Rollback

To rollback the migrations:

```sql
-- Drop policies
DROP POLICY IF EXISTS "Allow authenticated read access" ON documents;
DROP POLICY IF EXISTS "Allow authenticated insert access" ON documents;
DROP POLICY IF EXISTS "Allow authenticated update access" ON documents;
DROP POLICY IF EXISTS "Allow authenticated delete access" ON documents;

-- Drop functions
DROP FUNCTION IF EXISTS similarity_search;
DROP FUNCTION IF EXISTS get_document_stats;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;

-- Drop table (this will also drop indexes)
DROP TABLE IF EXISTS documents;
```

## Next Steps

After setting up the database schema:

1. Configure your application's database connection
2. Test the connection using the application's health check
3. Begin implementing the storage adapter to interact with this schema
4. Run integration tests to verify the complete workflow