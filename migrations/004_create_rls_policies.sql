-- Migration: Create Row Level Security policies
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
GRANT USAGE ON SEQUENCE documents_id_seq TO authenticated;