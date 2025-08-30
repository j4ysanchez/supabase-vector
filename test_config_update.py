#!/usr/bin/env python3
"""Test the updated configuration with separate anon and service keys."""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_config, get_supabase_config

def test_config_update():
    """Test that the configuration properly loads both keys."""
    
    print("🔍 Testing Updated Configuration")
    print("=" * 50)
    
    try:
        # Test the main config
        config = get_config()
        print("✅ Main config loaded successfully")
        
        print(f"📡 Supabase URL: {config.supabase_url}")
        print(f"🔑 Anon Key: {config.supabase_anon_key[:20]}...")
        print(f"🔐 Service Key: {config.supabase_service_key[:20]}...")
        print(f"📋 Table: {config.supabase_table}")
        
        # Test the Supabase config helper
        supabase_config = get_supabase_config()
        print("\n✅ Supabase config helper loaded successfully")
        
        print(f"📡 URL: {supabase_config.url}")
        print(f"🔑 Anon Key: {supabase_config.anon_key[:20]}...")
        print(f"🔐 Service Key: {supabase_config.service_key[:20]}...")
        print(f"📋 Table: {supabase_config.table_name}")
        
        # Verify they're different keys
        if supabase_config.anon_key != supabase_config.service_key:
            print("\n✅ Anon key and service key are different (correct)")
        else:
            print("\n⚠️  Warning: Anon key and service key are the same")
        
        # Check environment variables directly
        print("\n🔍 Environment Variables:")
        anon_key_env = os.getenv('SUPABASE_KEY', 'Not set')
        service_key_env = os.getenv('SUPABASE_SERVICE_KEY', 'Not set')
        
        print(f"SUPABASE_KEY: {anon_key_env[:20] if anon_key_env != 'Not set' else anon_key_env}...")
        print(f"SUPABASE_SERVICE_KEY: {service_key_env[:20] if service_key_env != 'Not set' else service_key_env}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_update()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Configuration update successful!")
        print("✅ Both anon key and service key are properly loaded")
    else:
        print("💥 Configuration update failed!")
        print("❌ Check your .env file and configuration")
    
    sys.exit(0 if success else 1)