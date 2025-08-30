#!/usr/bin/env python3
"""Test script to verify Supabase authentication and RLS bypass."""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_supabase_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_supabase_auth():
    """Test Supabase authentication and RLS bypass."""
    
    logger.info("=== Testing Supabase Authentication ===")
    
    # Get configuration
    config = get_supabase_config()
    logger.info(f"Supabase URL: {config.url}")
    logger.info(f"Using service key: {config.service_key[:20]}...")
    
    try:
        from supabase import create_client
        
        # Create client with service key
        client = create_client(config.url, config.service_key)
        logger.info("✓ Supabase client created successfully")
        
        # Test basic connection
        logger.info("Testing basic connection...")
        response = client.table(config.table_name).select("count").limit(1).execute()
        logger.info(f"✓ Connection successful. Response: {response}")
        
        # Check if service role has bypass RLS permission
        logger.info("Checking service role permissions...")
        try:
            role_check = client.rpc('check_service_role_permissions').execute()
            logger.info(f"Service role permissions: {role_check}")
        except Exception as e:
            logger.warning(f"Could not check role permissions directly (function may not exist): {type(e).__name__}")
            logger.info("This is expected if the permission check function hasn't been created yet.")
        
        # Test insert with service key (should bypass RLS)
        logger.info("Testing insert with service key (should bypass RLS)...")
        test_data = {
            "filename": "auth_test.txt",
            "file_path": "/test/auth_test.txt", 
            "content_hash": "test_hash_123",
            "content": "Test content for authentication",
            "embedding": [0.1] * 768,  # 768-dimensional embedding
            "metadata": {"test": True}
        }
        
        insert_response = client.table(config.table_name).insert(test_data).execute()
        logger.info(f"✓ Insert successful: {insert_response}")
        
        # Clean up - delete the test record
        if insert_response.data:
            record_id = insert_response.data[0]['id']
            delete_response = client.table(config.table_name).delete().eq('id', record_id).execute()
            logger.info(f"✓ Cleanup successful: {delete_response}")
        
        logger.info("=== Authentication test completed successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"✗ Authentication test failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Provide specific guidance based on the error
        if "row-level security policy" in str(e).lower():
            logger.error("\n🔧 RLS BYPASS ISSUE DETECTED:")
            logger.error("The service role is not properly configured to bypass RLS.")
            logger.error("\n📋 TO FIX THIS:")
            logger.error("1. Open your Supabase Dashboard")
            logger.error("2. Go to SQL Editor")
            logger.error("3. Run the script: complete_service_role_setup.sql")
            logger.error("4. Or run: check_rls_permissions.sql to diagnose the issue")
            logger.error("\n🚀 Quick test: python quick_rls_test.py")
        elif "supabase" in str(e).lower() and "import" in str(e).lower():
            logger.error("\n📦 MISSING DEPENDENCY:")
            logger.error("Install Supabase client: pip install supabase")
        else:
            logger.error(f"\n🐛 UNEXPECTED ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_supabase_auth())
        
        if success:
            print("\n🎉 SUCCESS: Service role authentication is working!")
            print("🚀 You can now run: python examples/storage_demo.py")
        else:
            print("\n💥 FAILED: Service role needs configuration")
            print("📖 See the error messages above for specific instructions")
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error running test: {e}")
        sys.exit(1)