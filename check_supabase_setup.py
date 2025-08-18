#!/usr/bin/env python3
"""
Script to check Supabase setup and provide guidance.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def decode_jwt_payload(token):
    """Decode JWT payload to check token type."""
    try:
        import base64
        import json
        
        # JWT has 3 parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (second part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        
        decoded = base64.b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return None

def check_supabase_config():
    """Check Supabase configuration and provide guidance."""
    print("🔍 Checking Supabase Configuration")
    print("=" * 50)
    
    # Check URL
    url = os.getenv("SUPABASE_URL")
    if url:
        print(f"✅ SUPABASE_URL: {url}")
    else:
        print("❌ SUPABASE_URL not found")
        return False
    
    # Check keys
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    anon_key = os.getenv("SUPABASE_KEY")
    
    print(f"\n🔑 Key Configuration:")
    
    if service_key:
        print(f"✅ SUPABASE_SERVICE_KEY found")
        payload = decode_jwt_payload(service_key)
        if payload:
            role = payload.get('role', 'unknown')
            print(f"   Role: {role}")
            if role == 'service_role':
                print("   ✅ This is a service role key (good for testing)")
            else:
                print(f"   ⚠️  Expected 'service_role', got '{role}'")
    else:
        print("❌ SUPABASE_SERVICE_KEY not found")
    
    if anon_key:
        print(f"✅ SUPABASE_KEY found")
        payload = decode_jwt_payload(anon_key)
        if payload:
            role = payload.get('role', 'unknown')
            print(f"   Role: {role}")
            if role == 'anon':
                print("   ℹ️  This is an anonymous key (has RLS restrictions)")
            else:
                print(f"   ⚠️  Expected 'anon', got '{role}'")
    else:
        print("❌ SUPABASE_KEY not found")
    
    # Check table name
    table_name = os.getenv("SUPABASE_TABLE_NAME", "documents")
    print(f"\n📋 Table: {table_name}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if not service_key:
        print("   1. Get your service role key from Supabase dashboard:")
        print("      - Go to Settings → API")
        print("      - Copy the 'service_role' key")
        print("      - Add SUPABASE_SERVICE_KEY=your_key to .env")
    
    if not anon_key and not service_key:
        print("   2. You need at least one Supabase key configured")
    
    print("   3. For live testing, use the service role key")
    print("   4. Run the database migrations to create the table")
    print("   5. See SUPABASE_SETUP.md for detailed instructions")
    
    return service_key is not None or anon_key is not None

def test_connection():
    """Test connection to Supabase."""
    print(f"\n🧪 Testing Connection")
    print("=" * 50)
    
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print("❌ Missing URL or key")
            return False
        
        print("🔌 Attempting to connect...")
        client = create_client(url, key)
        
        # Try a simple query
        table_name = os.getenv("SUPABASE_TABLE_NAME", "documents")
        result = client.table(table_name).select("count", count="exact").limit(1).execute()
        
        print(f"✅ Connection successful!")
        print(f"   Table '{table_name}' has {result.count} records")
        
        return True
        
    except ImportError:
        print("❌ Supabase client not installed")
        print("   Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
        if "does not exist" in str(e):
            print("   💡 The table doesn't exist yet. Run the migrations!")
        elif "row-level security" in str(e):
            print("   💡 RLS policy issue. Use the service role key for testing.")
        elif "extension" in str(e):
            print("   💡 pgvector extension not enabled. Enable it in Supabase dashboard.")
        
        return False

def main():
    """Main function."""
    print("🚀 Supabase Setup Checker")
    print("=" * 50)
    
    # Check configuration
    config_ok = check_supabase_config()
    
    if config_ok:
        # Test connection
        connection_ok = test_connection()
        
        if connection_ok:
            print(f"\n🎉 Setup looks good! You can now run:")
            print(f"   python run_live_tests.py health")
            print(f"   python run_live_tests.py basic")
        else:
            print(f"\n📖 See SUPABASE_SETUP.md for setup instructions")
    else:
        print(f"\n📖 Please configure your environment variables first")
        print(f"   See SUPABASE_SETUP.md for detailed instructions")

if __name__ == "__main__":
    main()