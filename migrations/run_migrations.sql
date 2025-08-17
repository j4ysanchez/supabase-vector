-- Master migration script for Python CLI Vector DB
-- Description: Runs all migrations in the correct order to set up the complete schema
-- Usage: Execute this script in Supabase SQL Editor or via psql

-- Migration 001: Create documents table with vector support
\i 001_create_documents_table.sql

-- Migration 002: Create indexes for performance
\i 002_create_indexes.sql

-- Migration 003: Create utility functions and triggers
\i 003_create_functions.sql

-- Migration 004: Create Row Level Security policies
\i 004_create_rls_policies.sql

-- Verify the setup
SELECT 'Migration completed successfully. Documents table created with vector support.' as status;