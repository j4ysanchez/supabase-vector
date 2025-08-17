-- Migration: Create Row Level Security policies (FIXED VERSION)
-- Description: Add security policies for data protection
-- Requirements: 1.3, 5.2, 5.3

-- Enable Row Level Security on documents table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy to allow authenticated users to read all documents
CREATE POLICY "Allow authenticated read access" ON documents
    FOR SELECT
    TO authenticated
    USING (true);

-- Policy to allow authenticated users to insert documents
CREATE POLICY "Allow authenticated insert access" ON documents
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Policy to allow authenticated users to update documents they can read
CREATE POLICY "Allow authenticated update access" ON documents
    FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Policy to allow authenticated users to delete documents
CREATE POLICY "Allow authenticated delete access" ON documents
    FOR DELETE
    TO authenticated
    USING (true);

-- Grant necessary permissions to authenticated role
GRANT SELECT, INSERT, UPDATE, DELETE ON documents TO authenticated;
-- Note: No sequence grant needed since we use UUID primary keys with gen_random_uuid()

-- Verify RLS is enabled
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables 
WHERE tablename = 'documents';

-- Show created policies
SELECT 
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'documents'
ORDER BY policyname;