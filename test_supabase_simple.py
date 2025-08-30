#!/usr/bin/env python3
"""Simple synchronous test for Supabase authentication and RLS bypass."""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_supabase_config

def test_supabase_simple():
    """Simple synchronous test for Supabase authentication."""
    
    print("🔍 Testing Supabase Authentication (Simple Version)")
    print("=" * 50)
    
    # Get configuration
    config = get_supabase_config()
    print(f"📡 Supabase URL: {config.url}")
    print(f"🔑 Using service key: {config.service_key[:20]}...")
    print(f"📋 Table name: {config.table_name}")
    
    try:
        from supabase import create_client
        print("✅ Supabase library imported successfully")
        
        # Create client with service key
        client = create_client(config.url, config.service_key)
        print("✅ Supabase client created successfully")
        
        # Test basic connection
        print("\n🔗 Testing basic connection...")
        response = client.table(config.table_name).select("count").limit(1).execute()
        print(f"✅ Connection successful. Records in table: {response.data[0]['count'] if response.data else 'unknown'}")
        
        # Test insert with service key (should bypass RLS)
        print("\n📝 Testing insert with service key (should bypass RLS)...")
        test_data = {
            "filename": "simple_auth_test.txt",
            "file_path": "/test/simple_auth_test.txt", 
            "content_hash": "simple_test_hash_123",
            "content": "Simple test content for authentication",
            "embedding": [0.1] * 768,  # 768-dimensional embedding
            "metadata": {"test": True, "version": "simple"}
        }
        
        insert_response = client.table(config.table_name).insert(test_data).execute()
        
        if insert_response.data:
            record_id = insert_response.data[0]['id']
            print(f"✅ Insert successful! Record ID: {record_id}")
            
            # Clean up - delete the test record
            delete_response = client.table(config.table_name).delete().eq('id', record_id).execute()
            print("🧹 Test record cleaned up successfully")
            
            print("\n🎉 SUCCESS: Service role can bypass RLS!")
            return True
        else:
            print("❌ Insert failed - no data returned")
            return False
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 Install Supabase client: pip install supabase")
        return False
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Test failed: {error_msg}")
        
        if "row-level security policy" in error_msg.lower():
            print("\n🔧 RLS BYPASS ISSUE DETECTED:")
            print("The service role is not properly configured to bypass RLS.")
            print("\n📋 TO FIX THIS:")
            print("1. Open your Supabase Dashboard")
            print("2. Go to SQL Editor") 
            print("3. Run the script: complete_service_role_setup.sql")
            print("4. Or run: check_rls_permissions.sql to diagnose")
            print("\n🚀 Alternative: python quick_rls_test.py")
        elif "unauthorized" in error_msg.lower():
            print("\n🔑 AUTHENTICATION ISSUE:")
            print("Check your service key in the .env file")
        else:
            print(f"\n🐛 Unexpected error: {error_msg}")
            print("Check your Supabase configuration and network connection")
        
        return False


if __name__ == "__main__":
    try:
        success = test_supabase_simple()
        
        print("\n" + "=" * 50)
        if success:
            print("🎯 RESULT: Authentication is working correctly!")
            print("🚀 You can now run: python examples/storage_demo.py")
        else:
            print("💥 RESULT: Authentication needs configuration")
            print("📖 Follow the instructions above to fix the issue")
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)