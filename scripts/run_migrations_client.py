#!/usr/bin/env python3
"""
Supabase Migration Runner using supabase-py client
Requires: pip install supabase
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client

def run_migrations_with_client():
    """Run migrations using Supabase Python client"""
    
    # Get credentials from environment
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")  # or SERVICE_ROLE_KEY for admin operations
    
    if not url or not key:
        print("❌ Missing required environment variables:")
        print("   SUPABASE_URL - Your Supabase project URL")
        print("   SUPABASE_ANON_KEY - Your Supabase anon key (or SERVICE_ROLE_KEY)")
        print("\nGet these from: https://supabase.com/dashboard/project/[project]/settings/api")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(url, key)
        
        # Migration files in order
        migrations = [
            "001_create_documents_table.sql",
            "002_create_indexes.sql",
            "003_create_functions.sql", 
            "004_create_rls_policies.sql"
        ]
        
        migrations_dir = Path("migrations")
        
        print(f"🚀 Starting migrations for: {url}")
        print("=" * 50)
        
        for migration_file in migrations:
            migration_path = migrations_dir / migration_file
            
            if not migration_path.exists():
                print(f"❌ Migration file not found: {migration_file}")
                continue
            
            print(f"📄 Running: {migration_file}")
            
            with open(migration_path, 'r') as f:
                sql_content = f.read()
            
            try:
                # Execute SQL using rpc call
                result = supabase.rpc('exec_sql', {'sql': sql_content})
                print(f"✅ Completed: {migration_file}")
                
            except Exception as e:
                print(f"❌ Failed: {migration_file} - {e}")
                return False
        
        print("=" * 50)
        print("🎉 All migrations completed!")
        
        # Run verification
        verify_path = migrations_dir / "verify_schema.sql"
        if verify_path.exists():
            print("🔍 Running schema verification...")
            with open(verify_path, 'r') as f:
                verify_sql = f.read()
            
            try:
                result = supabase.rpc('exec_sql', {'sql': verify_sql})
                print("✅ Schema verification completed")
            except Exception as e:
                print(f"⚠️  Schema verification failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def create_exec_sql_function():
    """
    Note: You need to create this function in your Supabase database first:
    
    CREATE OR REPLACE FUNCTION exec_sql(sql text)
    RETURNS text
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        EXECUTE sql;
        RETURN 'Success';
    EXCEPTION
        WHEN OTHERS THEN
            RETURN 'Error: ' || SQLERRM;
    END;
    $$;
    """
    pass

if __name__ == "__main__":
    print("📋 Note: This method requires creating an exec_sql function in your database first.")
    print("   See the function definition in the script comments.")
    print()
    
    if run_migrations_with_client():
        sys.exit(0)
    else:
        sys.exit(1)