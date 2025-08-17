# Migration Execution Scripts

This directory contains multiple ways to execute the Supabase migrations without manually copy-pasting in the dashboard.

## Quick Comparison

| Method | Best For | Requirements | Pros | Cons |
|--------|----------|--------------|------|------|
| **Management API** | CI/CD, Automation | Access token | Programmatic, reliable | Requires token setup |
| **Supabase CLI** | Local development | CLI installed | Easy, integrated | Requires project linking |
| **Direct psql** | Any environment | PostgreSQL client | Universal, fast | Need connection string |
| **Python Client** | Python projects | supabase-py | Integrated with app | Limited SQL execution |

## Option 1: Management API (Recommended)

### Setup
```bash
# Get your credentials from Supabase Dashboard > Settings > API
export SUPABASE_PROJECT_REF="your-project-ref"
export SUPABASE_ACCESS_TOKEN="your-access-token"

# Install dependencies
pip install requests

# Run migrations
python scripts/run_migrations.py
```

### Getting Access Token
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Navigate to your project
3. Go to Settings > API
4. Copy the "Project Reference" and generate an "Access Token"

## Option 2: Supabase CLI

### Setup
```bash
# Install Supabase CLI
npm install -g supabase

# Login and link project
supabase login
supabase link --project-ref YOUR_PROJECT_REF

# Make script executable and run
chmod +x scripts/run_migrations_cli.sh
./scripts/run_migrations_cli.sh
```

## Option 3: Direct PostgreSQL (psql)

### Setup
```bash
# Install PostgreSQL client (if not already installed)
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql-client

# Get connection string from Supabase Dashboard > Settings > Database
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:5432/postgres"

# Make script executable and run
chmod +x scripts/run_migrations_psql.sh
./scripts/run_migrations_psql.sh
```

## Option 4: Python Supabase Client

### Setup
```bash
# Install supabase client
pip install supabase

# Set environment variables
export SUPABASE_URL="https://your-project-ref.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"  # or SERVICE_ROLE_KEY

# First, create the exec_sql function in your database (see script comments)
# Then run migrations
python scripts/run_migrations_client.py
```

## Environment Variables Reference

Create a `.env` file in your project root:

```bash
# For Management API
SUPABASE_PROJECT_REF=your-project-ref
SUPABASE_ACCESS_TOKEN=your-access-token

# For Direct Connection
DATABASE_URL=postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:5432/postgres

# For Python Client
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure your access token has sufficient privileges
   - For RLS operations, you may need the service role key

2. **Connection Timeout**
   - Check your network connection
   - Verify the project reference and credentials

3. **SQL Execution Errors**
   - Check the migration file syntax
   - Ensure prerequisites (like extensions) are available

4. **Vector Extension Not Available**
   - pgvector should be available by default in Supabase
   - If not, contact Supabase support

### Manual Fallback

If all automated methods fail, you can still copy-paste the migrations:

1. Open [Supabase SQL Editor](https://supabase.com/dashboard/project/_/sql)
2. Copy contents of each migration file in order:
   - `migrations/001_create_documents_table.sql`
   - `migrations/002_create_indexes.sql`
   - `migrations/003_create_functions.sql`
   - `migrations/004_create_rls_policies.sql`
3. Execute each one
4. Run `migrations/verify_schema.sql` to confirm

## Security Notes

- Never commit access tokens or passwords to version control
- Use environment variables or secure secret management
- The service role key has admin privileges - use carefully
- Consider using different credentials for different environments

## Next Steps

After running migrations successfully:

1. Test the connection from your application
2. Run the verification script to ensure everything works
3. Begin implementing the storage adapter
4. Set up your application's database configuration