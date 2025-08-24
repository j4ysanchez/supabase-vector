#!/usr/bin/env python3
"""
Simple Supabase test that works with anonymous key.
This test will help you explore your database and validate the setup.
"""

import os
import asyncio
import pytest
from dotenv import load_dotenv
from supabase import create_client
from uuid import uuid4

# Load environment variables
load_dotenv()

@pytest.mark.asyncio
async def test_supabase_connection():
    """Test basic Supabase connection and table access."""
    print("🧪 Testing Supabase Connection")
    print("=" * 40)
    
    # Get configuration
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    table_name = os.getenv("SUPABASE_TABLE_NAME", "documents")
    
    print(f"URL: {url}")
    print(f"Table: {table_name}")
    print(f"Key type: {'Service Role' if 'SUPABASE_SERVICE_KEY' in os.environ else 'Anonymous'}")
    
    # Create client
    client = create_client(url, key)
    
    # Test 1: Check table exists and get count
    print(f"\n📊 Checking table '{table_name}'...")
    try:
        result = client.table(table_name).select("count", count="exact").limit(1).execute()
        print(f"✅ Table exists with {result.count} records")
    except Exception as e:
        print(f"❌ Error accessing table: {e}")
        return
    
    # Test 2: Try to read existing data
    print(f"\n📖 Reading existing data...")
    try:
        result = client.table(table_name).select("*").limit(5).execute()
        if result.data:
            print(f"✅ Found {len(result.data)} records:")
            for i, record in enumerate(result.data):
                print(f"   {i+1}. {record.get('filename', 'Unknown')} (ID: {str(record.get('id', 'Unknown'))[:8]}...)")
        else:
            print("ℹ️  No records found in table")
    except Exception as e:
        print(f"❌ Error reading data: {e}")
    
    # Test 3: Try to insert a simple record (this might fail with RLS)
    print(f"\n📝 Testing data insertion...")
    test_record = {
        "filename": "test_connection.txt",
        "file_path": "/test/connection.txt",
        "content_hash": f"test_hash_{uuid4().hex[:8]}",
        "chunk_index": 0,
        "content": "This is a test record to verify database connectivity.",
        "embedding": [0.1, 0.2, 0.3] + [0.0] * 765,  # 768-dimensional vector
        "metadata": {
            "test": True,
            "created_by": "connection_test"
        }
    }
    
    try:
        result = client.table(table_name).insert(test_record).execute()
        if result.data:
            record_id = result.data[0]['id']
            print(f"✅ Successfully inserted test record (ID: {record_id})")
            
            # Clean up - delete the test record
            print(f"🧹 Cleaning up test record...")
            delete_result = client.table(table_name).delete().eq('id', record_id).execute()
            if delete_result.data:
                print(f"✅ Test record deleted successfully")
            else:
                print(f"⚠️  Test record may not have been deleted")
        else:
            print(f"❌ Insert failed - no data returned")
    except Exception as e:
        print(f"❌ Insert failed: {e}")
        if "row-level security" in str(e).lower():
            print(f"💡 This is expected with anonymous key. Use service role key for testing.")
        elif "does not exist" in str(e).lower():
            print(f"💡 Table doesn't exist. Run the migration scripts.")
    
    # Test 4: Test vector similarity search function (if it exists)
    print(f"\n🔍 Testing similarity search function...")
    try:
        # Test the similarity_search function
        query_embedding = [0.1, 0.2, 0.3] + [0.0] * 765
        result = client.rpc('similarity_search', {
            'query_embedding': query_embedding,
            'similarity_threshold': 0.5,
            'max_results': 5
        }).execute()
        
        print(f"✅ Similarity search function exists")
        if result.data:
            print(f"   Found {len(result.data)} similar documents")
        else:
            print(f"   No similar documents found (expected with empty table)")
    except Exception as e:
        print(f"❌ Similarity search failed: {e}")
        if "does not exist" in str(e).lower():
            print(f"💡 Similarity search function not created. Run migration 3.")
    
    print(f"\n🎉 Connection test completed!")

def main():
    """Main function."""
    asyncio.run(test_supabase_connection())

if __name__ == "__main__":
    main()