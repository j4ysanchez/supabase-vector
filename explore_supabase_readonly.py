#!/usr/bin/env python3
"""
Read-only Supabase exploration script.
Works with anonymous key to explore existing data.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def explore_database():
    """Explore the Supabase database in read-only mode."""
    print("🔍 Exploring Supabase Database (Read-Only)")
    print("=" * 50)
    
    # Get configuration
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    table_name = os.getenv("SUPABASE_TABLE_NAME", "documents")
    
    # Create client
    client = create_client(url, key)
    
    # Get table statistics
    print(f"📊 Table Statistics")
    print("-" * 30)
    try:
        result = client.table(table_name).select("count", count="exact").limit(1).execute()
        total_records = result.count
        print(f"Total records: {total_records}")
        
        if total_records == 0:
            print("ℹ️  Database is empty. No documents to explore.")
            print("\n💡 To add test data:")
            print("   1. Get your service role key from Supabase dashboard")
            print("   2. Add SUPABASE_SERVICE_KEY to your .env file")
            print("   3. Run: python run_live_tests.py sample")
            return
        
        # Get unique filenames
        result = client.table(table_name).select("filename").execute()
        filenames = list(set(record['filename'] for record in result.data))
        print(f"Unique documents: {len(filenames)}")
        
        # Get records with embeddings
        result = client.table(table_name).select("id").not_.is_("embedding", "null").execute()
        records_with_embeddings = len(result.data)
        print(f"Records with embeddings: {records_with_embeddings}")
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        return
    
    # Show recent documents
    print(f"\n📋 Recent Documents")
    print("-" * 30)
    try:
        result = client.table(table_name)\
            .select("filename, content_hash, chunk_index, content, metadata, created_at")\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
        
        if result.data:
            for i, record in enumerate(result.data, 1):
                print(f"\n{i}. {record['filename']}")
                print(f"   Hash: {record['content_hash']}")
                print(f"   Chunk: {record['chunk_index']}")
                print(f"   Content: {record['content'][:100]}...")
                print(f"   Created: {record.get('created_at', 'Unknown')}")
                
                # Show metadata
                metadata = record.get('metadata', {})
                if metadata:
                    print(f"   Metadata: {metadata}")
        else:
            print("No documents found")
            
    except Exception as e:
        print(f"❌ Error reading documents: {e}")
    
    # Show unique content hashes (documents)
    print(f"\n📄 Document Groups (by content hash)")
    print("-" * 30)
    try:
        result = client.table(table_name)\
            .select("content_hash, filename")\
            .execute()
        
        # Group by content hash
        documents = {}
        for record in result.data:
            hash_key = record['content_hash']
            if hash_key not in documents:
                documents[hash_key] = {
                    'filename': record['filename'],
                    'chunks': 0
                }
            documents[hash_key]['chunks'] += 1
        
        for i, (hash_key, info) in enumerate(documents.items(), 1):
            print(f"{i}. {info['filename']}")
            print(f"   Hash: {hash_key}")
            print(f"   Chunks: {info['chunks']}")
            
    except Exception as e:
        print(f"❌ Error grouping documents: {e}")
    
    # Test similarity search with sample data
    print(f"\n🔍 Testing Similarity Search")
    print("-" * 30)
    try:
        # Create a sample query embedding
        query_embedding = [0.1, 0.2, 0.3] + [0.0] * 765
        
        result = client.rpc('similarity_search', {
            'query_embedding': query_embedding,
            'similarity_threshold': 0.1,  # Low threshold to find any matches
            'max_results': 5
        }).execute()
        
        if result.data:
            print(f"Found {len(result.data)} similar documents:")
            for i, doc in enumerate(result.data, 1):
                print(f"{i}. {doc['filename']} (similarity: {doc['similarity']:.3f})")
                print(f"   Content: {doc['content'][:80]}...")
        else:
            print("No similar documents found")
            print("💡 This is expected if there are no documents with embeddings")
            
    except Exception as e:
        print(f"❌ Similarity search failed: {e}")
    
    # Show database schema info
    print(f"\n🏗️  Database Schema Information")
    print("-" * 30)
    print("Table: documents")
    print("Columns:")
    print("  - id (UUID, Primary Key)")
    print("  - filename (TEXT)")
    print("  - file_path (TEXT)")
    print("  - content_hash (TEXT)")
    print("  - chunk_index (INTEGER)")
    print("  - content (TEXT)")
    print("  - embedding (VECTOR(768))")
    print("  - metadata (JSONB)")
    print("  - created_at (TIMESTAMP)")
    print("  - updated_at (TIMESTAMP)")
    
    print(f"\nFunctions:")
    print("  - similarity_search(query_embedding, threshold, max_results, filename_filter)")
    
    print(f"\n🎯 Next Steps")
    print("-" * 30)
    print("To fully test the database:")
    print("1. Get your service role key from Supabase dashboard")
    print("2. Add SUPABASE_SERVICE_KEY to .env file")
    print("3. Run: python run_live_tests.py sample")
    print("4. Run: python run_live_tests.py basic")
    print("5. Explore data in Supabase dashboard")

def main():
    """Main function."""
    explore_database()

if __name__ == "__main__":
    main()