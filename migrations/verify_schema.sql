-- Schema verification script
-- Description: Verify that all database objects were created correctly
-- Usage: Run this after executing the migrations to confirm setup

-- Check if vector extension is enabled
SELECT 
    extname as extension_name,
    extversion as version
FROM pg_extension 
WHERE extname = 'vector';

-- Check if documents table exists with correct structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'documents' 
ORDER BY ordinal_position;

-- Check if all indexes were created
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'documents'
ORDER BY indexname;

-- Check if functions were created
SELECT 
    routine_name,
    routine_type
FROM information_schema.routines 
WHERE routine_name IN (
    'update_updated_at_column',
    'get_document_stats',
    'similarity_search'
)
ORDER BY routine_name;

-- Check if RLS is enabled
SELECT 
    tablename,
    rowsecurity
FROM pg_tables 
WHERE tablename = 'documents';

-- Check RLS policies
SELECT 
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies 
WHERE tablename = 'documents'
ORDER BY policyname;

-- Test basic functionality with a sample insert and query
-- (This will be commented out by default to avoid test data in production)
/*
INSERT INTO documents (filename, file_path, content_hash, content) 
VALUES ('test.txt', '/path/to/test.txt', 'sample_hash', 'Sample content for testing');

SELECT id, filename, content, created_at 
FROM documents 
WHERE filename = 'test.txt';

DELETE FROM documents WHERE filename = 'test.txt';
*/

SELECT 'Schema verification completed. Check results above.' as status;