#!/bin/bash
# Supabase CLI Migration Runner
# Requires: supabase CLI installed and project linked

set -e

echo "🚀 Running migrations via Supabase CLI"
echo "======================================"

# Check if supabase CLI is available
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Install it first:"
    echo "   npm install -g supabase"
    echo "   or visit: https://supabase.com/docs/guides/cli"
    exit 1
fi

# Check if project is linked
if [ ! -f "supabase/config.toml" ]; then
    echo "❌ Supabase project not linked. Run:"
    echo "   supabase login"
    echo "   supabase link --project-ref YOUR_PROJECT_REF"
    exit 1
fi

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
        supabase db reset --db-url "$(supabase status | grep 'DB URL' | awk '{print $3}')" --file "$migration"
        echo "✅ Completed: $migration"
    else
        echo "❌ File not found: $migration"
        exit 1
    fi
done

echo "======================================"
echo "🎉 All migrations completed!"

# Run verification
if [ -f "migrations/verify_schema.sql" ]; then
    echo "🔍 Running schema verification..."
    supabase db reset --db-url "$(supabase status | grep 'DB URL' | awk '{print $3}')" --file "migrations/verify_schema.sql"
fi