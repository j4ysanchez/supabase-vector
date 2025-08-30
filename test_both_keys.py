#!/usr/bin/env python3
"""Test both anon key and service key to demonstrate RLS behavior."""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_supabase_config

def test_both_keys():
    """Test both anon key and service key to show RLS behavior."""
    
    print("🔍 Testing Both Supabase Keys")
    print("=" * 60)
    
    config = get_supabase_config()
    
    print(f"📡 Supabase URL: {config.url}")
    print(f"📋 Table: {config.table_name}")
    print(f"🔑 Anon Key: {config.anon_key[:20]}...")
    print(f"🔐 Service Key: {config.service_key[:20]}...")
    
    try:
        from supabase import create_client
        print("✅ Supabase library imported successfully")
        
        # Test data
        test_data = {
            "filename": "dual_key_test.txt",
            "file_path": "/test/dual_key_test.txt", 
            "content_hash": "dual_key_test_hash",
            "content": "Test content for dual key testing",
            "embedding": [0.1] * 768,  # 768-dimensional embedding
            "metadata": {"test": "dual_key", "timestamp": "2025-01-01"}
        }
        
        # ===== TEST 1: Service Key (Should Work) =====
        print(f"\n🔐 TEST 1: Service Key (Should Bypass RLS)")
        print("-" * 40)
        
        service_client = create_client(config.url, config.service_key)
        print("✅ Service client created")
        
        try:
            # Test connection
            response = service_client.table(config.table_name).select("count").limit(1).execute()
            print(f"✅ Service key connection successful. Records: {response.data[0]['count'] if response.data else 'unknown'}")
            
            # Test insert
            print("📝 Attempting insert with service key...")
            insert_response = service_client.table(config.table_name).insert(test_data).execute()
            
            if insert_response.data:
                record_id = insert_response.data[0]['id']
                print(f"✅ SUCCESS: Service key inserted record {record_id}")
                
                # Clean up
                service_client.table(config.table_name).delete().eq('id', record_id).execute()
                print("🧹 Test record cleaned up")
                service_key_works = True
            else:
                print("❌ Service key insert failed - no data returned")
                service_key_works = False
                
        except Exception as e:
            print(f"❌ Service key failed: {e}")
            service_key_works = False
        
        # ===== TEST 2: Anon Key (Should Fail with RLS) =====
        print(f"\n🔑 TEST 2: Anon Key (Should Be Blocked by RLS)")
        print("-" * 40)
        
        if config.anon_key != config.service_key:
            anon_client = create_client(config.url, config.anon_key)
            print("✅ Anon client created")
            
            try:
                # Test connection (should work for reading)
                response = anon_client.table(config.table_name).select("count").limit(1).execute()
                print(f"✅ Anon key connection successful. Records: {response.data[0]['count'] if response.data else 'unknown'}")
                
                # Test insert (should fail with RLS)
                print("📝 Attempting insert with anon key...")
                insert_response = anon_client.table(config.table_name).insert(test_data).execute()
                
                if insert_response.data:
                    record_id = insert_response.data[0]['id']
                    print(f"⚠️  UNEXPECTED: Anon key was able to insert record {record_id}")
                    print("   This suggests RLS might be disabled or misconfigured")
                    
                    # Clean up
                    anon_client.table(config.table_name).delete().eq('id', record_id).execute()
                    print("🧹 Test record cleaned up")
                    anon_key_blocked = False
                else:
                    print("❌ Anon key insert failed - no data returned")
                    anon_key_blocked = True
                    
            except Exception as e:
                error_msg = str(e)
                if "row-level security policy" in error_msg.lower():
                    print("✅ EXPECTED: Anon key correctly blocked by RLS")
                    anon_key_blocked = True
                else:
                    print(f"❌ Anon key failed with unexpected error: {e}")
                    anon_key_blocked = False
        else:
            print("⏭️  SKIPPED: Anon key and service key are the same")
            anon_key_blocked = None
        
        # ===== SUMMARY =====
        print(f"\n📊 SUMMARY")
        print("=" * 60)
        
        if service_key_works:
            print("✅ Service Key: Can bypass RLS (CORRECT)")
        else:
            print("❌ Service Key: Cannot bypass RLS (NEEDS CONFIGURATION)")
        
        if anon_key_blocked is True:
            print("✅ Anon Key: Blocked by RLS (CORRECT)")
        elif anon_key_blocked is False:
            print("⚠️  Anon Key: Not blocked by RLS (RLS may be disabled)")
        else:
            print("⏭️  Anon Key: Not tested (same as service key)")
        
        # Overall result
        if service_key_works and (anon_key_blocked is True or anon_key_blocked is None):
            print("\n🎉 OVERALL: Configuration is working correctly!")
            return True
        else:
            print("\n🔧 OVERALL: Configuration needs adjustment")
            if not service_key_works:
                print("   - Service key needs RLS bypass configuration")
            if anon_key_blocked is False:
                print("   - RLS policies may need review")
            return False
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 Install Supabase client: pip install supabase")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_both_keys()
        
        print("\n" + "=" * 60)
        if success:
            print("🎯 RESULT: Both keys are working as expected!")
            print("🚀 You can now run: python examples/storage_demo.py")
        else:
            print("💥 RESULT: Key configuration needs adjustment")
            print("📖 Run complete_service_role_setup.sql in Supabase SQL Editor")
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)