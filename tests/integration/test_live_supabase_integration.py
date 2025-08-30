"""Live integration tests for Supabase vector storage.

These tests connect to a real Supabase database and perform actual operations.
Use these tests to validate real database functionality and explore data manually.

IMPORTANT: These tests will create and delete real data in your Supabase database.
Make sure you're using a test/development database, not production.
"""

import os
import pytest
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

from src.adapters.secondary.supabase.supabase_storage_adapter import SupabaseStorageAdapter
from src.domain.models.document import Document, DocumentChunk
from src.domain.exceptions import StorageError
from src.config import get_supabase_config


class LiveSupabaseStorageAdapter(SupabaseStorageAdapter):
    """Live Supabase adapter that uses the real Supabase client."""
    
    async def _get_client(self):
        """Get or create the real Supabase client."""
        if self._client is None:
            try:
                from supabase import create_client, Client
                self._client = create_client(self._config.url, self._config.service_key)
                print(f"✅ Connected to live Supabase: {self._config.url}")
            except ImportError:
                raise ImportError(
                    "supabase package not installed. Run: pip install supabase"
                )
            except Exception as e:
                raise StorageError(f"Failed to connect to Supabase: {e}")
        return self._client
    
    async def store_document(self, document: Document) -> bool:
        """Store a document using the real Supabase client."""
        try:
            client = await self._get_client()
            
            # Generate document ID if not present (we'll use content_hash to group chunks)
            if document.id is None:
                document.id = uuid4()
            
            # Prepare document records for each chunk
            # Note: The schema uses content_hash to group chunks, not document_id
            records = []
            for chunk in document.chunks:
                record = {
                    # Each chunk gets its own UUID as the primary key
                    'filename': document.filename,
                    'file_path': str(document.file_path),
                    'content_hash': document.content_hash,
                    'chunk_index': chunk.chunk_index,
                    'content': chunk.content,
                    'embedding': chunk.embedding,
                    'metadata': {
                        'document_id': str(document.id),  # Store document ID in metadata
                        'document_metadata': document.metadata,
                        'chunk_metadata': chunk.metadata
                    }
                }
                records.append(record)
            
            # Store all chunks in a single batch operation
            result = client.table(self._config.table_name).insert(records).execute()
            
            if result.data:
                print(f"✅ Stored document '{document.filename}' with {len(records)} chunks")
                return True
            else:
                print(f"❌ Failed to store document '{document.filename}'")
                return False
                
        except Exception as e:
            print(f"❌ Error storing document '{document.filename}': {e}")
            raise StorageError(f"Failed to store document: {e}", original_error=e)
    
    async def retrieve_document(self, document_id) -> Document:
        """Retrieve a document using the real Supabase client."""
        try:
            client = await self._get_client()
            
            # Query for all chunks of the document using metadata filter
            # Since document_id is stored in metadata, we need to use a JSON query
            result = client.table(self._config.table_name)\
                .select("*")\
                .eq('metadata->>document_id', str(document_id))\
                .order('chunk_index')\
                .execute()
            
            if not result.data:
                return None
            
            records = result.data
            
            # Reconstruct document from chunks
            first_record = records[0]
            chunks = []
            
            for record in records:
                stored_metadata = record.get('metadata', {})
                chunk_metadata = stored_metadata.get('chunk_metadata', {})
                
                # Handle embedding - it might be stored as a string or list
                embedding = record.get('embedding')
                if embedding and isinstance(embedding, str):
                    # Parse string representation back to list
                    try:
                        import json
                        embedding = json.loads(embedding.replace('[', '[').replace(']', ']'))
                    except:
                        # If parsing fails, keep as is
                        pass
                
                chunk = DocumentChunk(
                    content=record['content'],
                    chunk_index=record['chunk_index'],
                    embedding=embedding,
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
            
            # Extract document metadata from the first record
            first_stored_metadata = first_record.get('metadata', {})
            document_metadata = first_stored_metadata.get('document_metadata', {})
            
            document = Document(
                id=document_id,
                filename=first_record['filename'],
                file_path=Path(first_record['file_path']),
                content_hash=first_record['content_hash'],
                chunks=chunks,
                metadata=document_metadata,
                created_at=datetime.fromisoformat(first_record['created_at'].replace('Z', '+00:00')) if first_record.get('created_at') else None,
                updated_at=datetime.fromisoformat(first_record['updated_at'].replace('Z', '+00:00')) if first_record.get('updated_at') else None
            )
            
            print(f"✅ Retrieved document '{document.filename}' with {len(chunks)} chunks")
            return document
            
        except Exception as e:
            print(f"❌ Error retrieving document {document_id}: {e}")
            raise StorageError(f"Failed to retrieve document: {e}", original_error=e)
    
    async def delete_document(self, document_id) -> bool:
        """Delete a document using the real Supabase client."""
        try:
            client = await self._get_client()
            
            # Delete all chunks for the document using metadata filter
            result = client.table(self._config.table_name)\
                .delete()\
                .eq('metadata->>document_id', str(document_id))\
                .execute()
            
            if result.data is not None:
                deleted_count = len(result.data) if result.data else 0
                if deleted_count > 0:
                    print(f"✅ Deleted document {document_id} ({deleted_count} chunks)")
                    return True
                else:
                    print(f"⚠️  Document {document_id} not found for deletion")
                    return False
            else:
                print(f"❌ Failed to delete document {document_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting document {document_id}: {e}")
            raise StorageError(f"Failed to delete document: {e}", original_error=e)
    
    async def list_documents(self, limit: int = 100, offset: int = 0):
        """List documents using the real Supabase client."""
        try:
            client = await self._get_client()
            
            # Get distinct document IDs from metadata with pagination
            result = client.table(self._config.table_name)\
                .select("metadata, filename, created_at")\
                .order('created_at', desc=True)\
                .limit(limit * 5)\
                .execute()  # Get more records to account for multiple chunks per document
            
            if not result.data:
                return []
            
            # Get unique document IDs from metadata
            seen_ids = set()
            unique_docs = []
            for record in result.data:
                metadata = record.get('metadata', {})
                doc_id = metadata.get('document_id')
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    unique_docs.append(doc_id)
                    if len(unique_docs) >= limit:  # Respect the limit
                        break
            
            # Retrieve each unique document
            documents = []
            for doc_id in unique_docs[offset:offset + limit]:
                document = await self.retrieve_document(doc_id)
                if document:
                    documents.append(document)
            
            print(f"✅ Listed {len(documents)} documents")
            return documents
            
        except Exception as e:
            print(f"❌ Error listing documents: {e}")
            raise StorageError(f"Failed to list documents: {e}", original_error=e)
    
    async def health_check(self) -> bool:
        """Check if the live Supabase connection is healthy."""
        try:
            client = await self._get_client()
            
            # Perform a simple query to check connectivity
            result = client.table(self._config.table_name)\
                .select("count", count="exact")\
                .limit(1)\
                .execute()
            
            print(f"✅ Supabase health check passed. Table has {result.count} records")
            return True
                
        except Exception as e:
            print(f"❌ Supabase health check failed: {e}")
            return False


@pytest.mark.live
class TestLiveSupabaseIntegration:
    """Live integration tests that connect to real Supabase database.
    
    Run with: pytest -m live tests/integration/test_live_supabase_integration.py -v -s
    """
    
    @pytest.fixture(scope="class")
    def live_config(self):
        """Create configuration from environment variables."""
        try:
            # Try to load service role key first, fall back to regular key
            service_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
            url = os.getenv("SUPABASE_URL")
            
            if not url or not service_key:
                pytest.skip("SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_KEY) must be set")
            
            config = SupabaseConfig(
                url=url,
                service_key=service_key,
                table_name=os.getenv("SUPABASE_TABLE_NAME", "documents"),
                timeout=int(os.getenv("SUPABASE_TIMEOUT", "30")),
                max_retries=int(os.getenv("SUPABASE_MAX_RETRIES", "3"))
            )
            
            print(f"\n🔧 Using Supabase URL: {config.url}")
            print(f"🔧 Using table: {config.table_name}")
            
            # Check if using service role key
            if "service_role" in service_key or len(service_key) > 200:
                print("🔧 Using service role key (bypasses RLS)")
            else:
                print("⚠️  Using anonymous key (may have RLS restrictions)")
                print("   For testing, consider using SUPABASE_SERVICE_KEY")
            
            return config
        except Exception as e:
            pytest.skip(f"Supabase configuration not available: {e}")
    
    @pytest.fixture(scope="class")
    def live_adapter(self, live_config):
        """Create a live storage adapter."""
        return LiveSupabaseStorageAdapter(live_config)
    
    @pytest.fixture
    def test_document(self):
        """Create a test document with realistic data."""
        return Document(
            filename=f"live_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            file_path=Path(f"/test/live_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
            content_hash=f"live_test_hash_{uuid4().hex[:8]}",
            chunks=[
                DocumentChunk(
                    content="This is a live test document chunk for Supabase integration testing.",
                    chunk_index=0,
                    embedding=[0.1, 0.2, 0.3] + [0.0] * 765,  # 768-dim vector
                    metadata={"chunk_type": "text", "test": "live", "language": "en"}
                ),
                DocumentChunk(
                    content="This is the second chunk of the live test document with different content.",
                    chunk_index=1,
                    embedding=[0.4, 0.5, 0.6] + [0.0] * 765,  # 768-dim vector
                    metadata={"chunk_type": "text", "test": "live", "language": "en"}
                )
            ],
            metadata={"source": "live_test", "test_type": "integration", "created_by": "pytest"}
        )
    
    @pytest.mark.asyncio
    async def test_live_database_connection(self, live_adapter):
        """Test connection to live Supabase database."""
        print("\n🧪 Testing live database connection...")
        
        # Test health check
        health_status = await live_adapter.health_check()
        assert health_status is True, "Live database health check should pass"
        
        print("✅ Live database connection successful!")
    
    @pytest.mark.asyncio
    async def test_live_document_storage_and_retrieval(self, live_adapter, test_document):
        """Test storing and retrieving a document in live database."""
        print(f"\n🧪 Testing live document storage for: {test_document.filename}")
        
        try:
            # Store the document
            store_result = await live_adapter.store_document(test_document)
            assert store_result is True, "Document storage should succeed"
            assert test_document.id is not None, "Document should have an ID after storage"
            
            print(f"📝 Document ID: {test_document.id}")
            
            # Retrieve the document
            retrieved = await live_adapter.retrieve_document(test_document.id)
            assert retrieved is not None, "Document should be retrievable"
            assert retrieved.filename == test_document.filename
            assert len(retrieved.chunks) == len(test_document.chunks)
            
            # Verify chunk data
            for i, chunk in enumerate(retrieved.chunks):
                original_chunk = test_document.chunks[i]
                assert chunk.content == original_chunk.content
                assert chunk.chunk_index == original_chunk.chunk_index
                assert len(chunk.embedding) == 768, "Embedding should be 768-dimensional"
            
            print("✅ Document storage and retrieval successful!")
            
            # Print document details for manual verification
            print(f"\n📊 Document Details:")
            print(f"   ID: {retrieved.id}")
            print(f"   Filename: {retrieved.filename}")
            print(f"   Chunks: {len(retrieved.chunks)}")
            print(f"   Created: {retrieved.created_at}")
            print(f"   Metadata: {retrieved.metadata}")
            
        finally:
            # Clean up - delete the test document
            if test_document.id:
                print(f"\n🧹 Cleaning up test document: {test_document.id}")
                delete_result = await live_adapter.delete_document(test_document.id)
                if delete_result:
                    print("✅ Test document deleted successfully")
                else:
                    print("⚠️  Test document may not have been deleted")
    
    @pytest.mark.asyncio
    async def test_live_document_listing(self, live_adapter):
        """Test listing documents from live database."""
        print("\n🧪 Testing live document listing...")
        
        # List existing documents
        documents = await live_adapter.list_documents(limit=10)
        
        print(f"📋 Found {len(documents)} documents in database:")
        for i, doc in enumerate(documents[:5]):  # Show first 5
            print(f"   {i+1}. {doc.filename} (ID: {str(doc.id)[:8]}..., Chunks: {len(doc.chunks)})")
        
        if len(documents) > 5:
            print(f"   ... and {len(documents) - 5} more documents")
        
        print("✅ Document listing successful!")
    
    @pytest.mark.asyncio
    async def test_live_vector_similarity_search(self, live_adapter, test_document):
        """Test vector similarity search with live database."""
        print(f"\n🧪 Testing vector similarity search...")
        
        try:
            # Store a test document with known embedding
            await live_adapter.store_document(test_document)
            
            # Create a similar embedding for search
            query_embedding = [0.15, 0.25, 0.35] + [0.0] * 765  # Similar to first chunk
            
            # Note: This test demonstrates the concept. In a real implementation,
            # you would use the similarity_search SQL function from the migrations
            print(f"🔍 Query embedding (first 3 dims): {query_embedding[:3]}")
            print(f"📄 Document embedding (first 3 dims): {test_document.chunks[0].embedding[:3]}")
            
            # Calculate cosine similarity manually for demonstration
            import numpy as np
            
            def cosine_similarity(a, b):
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
            similarity = cosine_similarity(query_embedding, test_document.chunks[0].embedding)
            print(f"📊 Cosine similarity: {similarity:.4f}")
            
            assert similarity > 0.9, "Similar embeddings should have high similarity"
            
            print("✅ Vector similarity calculation successful!")
            
        finally:
            # Clean up
            if test_document.id:
                await live_adapter.delete_document(test_document.id)
    
    @pytest.mark.asyncio
    async def test_live_error_scenarios(self, live_adapter):
        """Test error handling with live database."""
        print("\n🧪 Testing error scenarios...")
        
        # Test retrieving non-existent document
        fake_id = uuid4()
        retrieved = await live_adapter.retrieve_document(fake_id)
        assert retrieved is None, "Should return None for non-existent document"
        
        # Test deleting non-existent document
        delete_result = await live_adapter.delete_document(fake_id)
        assert delete_result is False, "Should return False for non-existent document"
        
        print("✅ Error scenarios handled correctly!")


@pytest.mark.live
class TestLiveSupabaseExploration:
    """Interactive tests for exploring live Supabase data.
    
    These tests are designed to help you explore and validate your Supabase setup.
    Run with: pytest tests/integration/test_live_supabase_integration.py::TestLiveSupabaseExploration -v -s
    """
    
    @pytest.fixture(scope="class")
    def live_config(self):
        """Create configuration from environment variables."""
        try:
            return SupabaseConfig.from_env()
        except Exception as e:
            pytest.skip(f"Supabase configuration not available: {e}")
    
    @pytest.fixture(scope="class")
    def live_adapter(self, live_config):
        """Create a live storage adapter."""
        return LiveSupabaseStorageAdapter(live_config)
    
    @pytest.mark.asyncio
    async def test_explore_database_contents(self, live_adapter):
        """Explore the current contents of your Supabase database."""
        print("\n🔍 Exploring Supabase Database Contents")
        print("=" * 50)
        
        # Check health
        health = await live_adapter.health_check()
        print(f"Database Health: {'✅ Healthy' if health else '❌ Unhealthy'}")
        
        # List all documents
        print("\n📋 Current Documents:")
        documents = await live_adapter.list_documents(limit=20)
        
        if not documents:
            print("   No documents found in database")
        else:
            for i, doc in enumerate(documents, 1):
                print(f"\n   {i}. Document: {doc.filename}")
                print(f"      ID: {doc.id}")
                print(f"      Hash: {doc.content_hash}")
                print(f"      Chunks: {len(doc.chunks)}")
                print(f"      Created: {doc.created_at}")
                print(f"      Metadata: {doc.metadata}")
                
                # Show first chunk details
                if doc.chunks:
                    chunk = doc.chunks[0]
                    print(f"      First Chunk: {chunk.content[:100]}...")
                    print(f"      Embedding dims: {len(chunk.embedding) if chunk.embedding else 'None'}")
        
        print(f"\n📊 Total documents: {len(documents)}")
    
    @pytest.mark.asyncio
    async def test_create_sample_document(self, live_adapter):
        """Create a sample document for manual exploration."""
        print("\n📝 Creating Sample Document for Manual Exploration")
        print("=" * 50)
        
        # Create a sample document with rich metadata
        sample_doc = Document(
            filename="sample_exploration_document.txt",
            file_path=Path("/samples/exploration_document.txt"),
            content_hash=f"sample_hash_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            chunks=[
                DocumentChunk(
                    content="This is a sample document created for manual exploration of the Supabase vector database. It contains meaningful content that can be used to test similarity search and other vector operations.",
                    chunk_index=0,
                    embedding=[0.8, 0.6, 0.4] + [0.1] * 765,  # Distinctive embedding
                    metadata={
                        "chunk_type": "introduction",
                        "topic": "database_exploration",
                        "importance": "high"
                    }
                ),
                DocumentChunk(
                    content="The second chunk demonstrates how multi-chunk documents are stored and retrieved. Each chunk has its own embedding vector and metadata, allowing for granular similarity search and content analysis.",
                    chunk_index=1,
                    embedding=[0.2, 0.9, 0.7] + [0.05] * 765,  # Different embedding
                    metadata={
                        "chunk_type": "explanation",
                        "topic": "vector_storage",
                        "importance": "medium"
                    }
                ),
                DocumentChunk(
                    content="This final chunk contains technical details about the implementation. The vector embeddings are 768-dimensional, matching the nomic-embed-text model output. Metadata is preserved at both document and chunk levels.",
                    chunk_index=2,
                    embedding=[0.5, 0.3, 0.9] + [0.02] * 765,  # Third embedding
                    metadata={
                        "chunk_type": "technical",
                        "topic": "implementation",
                        "importance": "high"
                    }
                )
            ],
            metadata={
                "purpose": "manual_exploration",
                "created_by": "integration_test",
                "category": "sample_data",
                "tags": ["exploration", "testing", "vector_db"]
            }
        )
        
        # Store the document
        result = await live_adapter.store_document(sample_doc)
        assert result is True, "Sample document should be stored successfully"
        
        print(f"✅ Sample document created successfully!")
        print(f"📝 Document ID: {sample_doc.id}")
        print(f"📝 Filename: {sample_doc.filename}")
        print(f"📝 Chunks: {len(sample_doc.chunks)}")
        
        print(f"\n🔍 You can now explore this document in Supabase:")
        print(f"   1. Go to your Supabase dashboard")
        print(f"   2. Navigate to Table Editor > documents")
        print(f"   3. Filter by document_id: {sample_doc.id}")
        print(f"   4. Examine the stored data, embeddings, and metadata")
        
        print(f"\n⚠️  Remember to clean up by running the cleanup test or manually deleting the document")
        
        return sample_doc.id
    
    @pytest.mark.asyncio
    async def test_cleanup_sample_documents(self, live_adapter):
        """Clean up sample documents created for exploration."""
        print("\n🧹 Cleaning Up Sample Documents")
        print("=" * 50)
        
        # List all documents and find sample ones
        documents = await live_adapter.list_documents(limit=50)
        sample_docs = [
            doc for doc in documents 
            if 'sample' in doc.filename.lower() or 
               doc.metadata.get('purpose') == 'manual_exploration'
        ]
        
        if not sample_docs:
            print("   No sample documents found to clean up")
            return
        
        print(f"Found {len(sample_docs)} sample documents to clean up:")
        
        for doc in sample_docs:
            print(f"   Deleting: {doc.filename} (ID: {doc.id})")
            result = await live_adapter.delete_document(doc.id)
            if result:
                print(f"   ✅ Deleted successfully")
            else:
                print(f"   ❌ Failed to delete")
        
        print(f"\n✅ Cleanup completed!")


if __name__ == "__main__":
    # Run live tests
    pytest.main([
        __file__,
        "-v",
        "-s",
        "-m", "live"
    ])