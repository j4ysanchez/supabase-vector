#!/bin/bash
# Direct PostgreSQL Migration Runner
# Requires: psql installed and database connection string

set -e

# Check for required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL environment variable not set"
    echo "   Format: postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:5432/postgres"
    echo "   Get this from: Supabase Dashboard > Settings > Database > Connection string"
    exit 1
fi

echo "🚀 Running migrations via psql"
echo "============================="

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ psql not found. Install PostgreSQL client:"
    echo "   macOS: brew install postgresql"
    echo "   Ubuntu: sudo apt-get install postgresql-client"
    exit 1
fi

# Test connection
echo "🔗 Testing database connection..."
if ! psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1; then
    echo "❌ Failed to connect to database. Check your DATABASE_URL"
    exit 1
fi
echo "✅ Database connection successful"

# Migration files in order
migrations=(
    "migrations/001_create_documents_table.sql"
    "migrations/002_create_indexes.sql"
    "migrations/003_create_functions.sql"
    "migrations/004_create_rls_policies.sql"
)

# Run each migration
for migration in "${migrations[@]}"; do
    if [ -f "$migration" ]; then
        echo "📄 Running: $migration"
        if psql "$DATABASE_URL" -f "$migration"; then
            echo "✅ Completed: $migration"
        else
            echo "❌ Failed: $migration"
            exit 1
        fi
    else
        echo "❌ File not found: $migration"
        exit 1
    fi
done

echo "============================="
echo "🎉 All migrations completed!"

# Run verification
if [ -f "migrations/verify_schema.sql" ]; then
    echo "🔍 Running schema verification..."
    psql "$DATABASE_URL" -f "migrations/verify_schema.sql"
fi