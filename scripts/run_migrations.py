#!/usr/bin/env python3
"""
Supabase Migration Runner
Executes SQL migrations via Supabase Management API
"""

import os
import requests
import sys
from pathlib import Path

def run_migration_via_api(project_ref: str, access_token: str, sql_content: str, migration_name: str):
    """Execute SQL migration via Supabase Management API"""
    
    url = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": sql_content
    }
    
    print(f"Running migration: {migration_name}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ {migration_name} completed successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ {migration_name} failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False

def main():
    # Get credentials from environment variables
    project_ref = os.getenv("SUPABASE_PROJECT_REF")
    access_token = os.getenv("SUPABASE_ACCESS_TOKEN")
    
    if not project_ref or not access_token:
        print("❌ Missing required environment variables:")
        print("   SUPABASE_PROJECT_REF - Your Supabase project reference")
        print("   SUPABASE_ACCESS_TOKEN - Your Supabase access token")
        print("\nGet these from: https://supabase.com/dashboard/project/[project]/settings/api")
        sys.exit(1)
    
    # Migration files in order
    migrations = [
        "001_create_documents_table.sql",
        "002_create_indexes.sql", 
        "003_create_functions.sql",
        "004_create_rls_policies.sql"
    ]
    
    migrations_dir = Path("migrations")
    
    if not migrations_dir.exists():
        print("❌ migrations directory not found")
        sys.exit(1)
    
    print(f"🚀 Starting migrations for project: {project_ref}")
    print("=" * 50)
    
    success_count = 0
    
    for migration_file in migrations:
        migration_path = migrations_dir / migration_file
        
        if not migration_path.exists():
            print(f"❌ Migration file not found: {migration_file}")
            continue
            
        with open(migration_path, 'r') as f:
            sql_content = f.read()
        
        if run_migration_via_api(project_ref, access_token, sql_content, migration_file):
            success_count += 1
        else:
            print(f"❌ Stopping migrations due to failure in {migration_file}")
            break
    
    print("=" * 50)
    print(f"✅ Completed {success_count}/{len(migrations)} migrations")
    
    if success_count == len(migrations):
        print("🎉 All migrations completed successfully!")
        
        # Run verification
        verify_path = migrations_dir / "verify_schema.sql"
        if verify_path.exists():
            print("\n🔍 Running schema verification...")
            with open(verify_path, 'r') as f:
                verify_sql = f.read()
            run_migration_via_api(project_ref, access_token, verify_sql, "Schema Verification")
    else:
        print("⚠️  Some migrations failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()