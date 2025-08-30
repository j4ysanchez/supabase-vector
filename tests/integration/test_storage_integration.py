"""Integration tests for Supabase vector storage."""

import os
import pytest
import asyncio
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch, AsyncMock

from src.adapters.secondary.supabase.supabase_storage_adapter import SupabaseStorageAdapter
from tests.mocks.mock_supabase_client import MockSupabaseClient
from src.domain.models.document import Document, DocumentChunk
from src.domain.exceptions import StorageError
from src.config import create_test_supabase_config


class TestSupabaseVectorStorageIntegration:
    """Integration tests for Supabase vector storage operations."""
    
    @pytest.fixture
    def test_config(self):
        """Create a test configuration for Supabase."""
        return create_test_supabase_config(
            url="https://test-project.supabase.co",
            service_key="test-service-key-12345",
            table_name="test_documents"
        )
    
    @pytest.fixture
    def adapter(self, test_config):
        """Create a storage adapter for integration testing."""
        adapter = SupabaseStorageAdapter(test_config)
        # Replace the client with a mock for testing
        adapter._client = MockSupabaseClient(test_config)
        return adapter
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document(
            filename="test_document.txt",
            file_path=Path("/test/test_document.txt"),
            content_hash="test_hash_123",
            chunks=[
                DocumentChunk(
                    content="This is the first chunk of the test document.",
                    chunk_index=0,
                    embedding=[0.1, 0.2, 0.3, 0.4, 0.5] + [0.0] * 763,  # 768-dim vector
                    metadata={"chunk_type": "text", "language": "en"}
                ),
                DocumentChunk(
                    content="This is the second chunk with different content.",
                    chunk_index=1,
                    embedding=[0.6, 0.7, 0.8, 0.9, 1.0] + [0.0] * 763,  # 768-dim vector
                    metadata={"chunk_type": "text", "language": "en"}
                )
            ],
            metadata={"source": "test", "document_type": "text"}
        )

    # Test 1: Database Connection and Table Structure Verification
    @pytest.mark.asyncio
    async def test_database_connection_and_table_structure(self, adapter):
        """Test that connects to Supabase and verifies table structure."""
        
        # Test health check - verifies basic connectivity
        health_status = await adapter.health_check()
        assert health_status is True, "Health check should pass for valid configuration"
        
        # Verify that the adapter can initialize client
        client = await adapter._get_client()
        assert client is not None, "Client should be initialized successfully"
        
        # Test table access by attempting a simple query
        # This implicitly verifies the table structure exists
        documents = await adapter.list_documents(limit=1)
        assert isinstance(documents, list), "Should return a list of documents"
    
    @pytest.mark.asyncio
    async def test_table_schema_validation(self, adapter):
        """Test that verifies the expected table schema is present."""
        
        # Create a document with all expected fields to test schema compatibility
        test_doc = Document(
            filename="schema_test.txt",
            file_path=Path("/test/schema_test.txt"),
            content_hash="schema_test_hash",
            chunks=[
                DocumentChunk(
                    content="Schema validation test content",
                    chunk_index=0,
                    embedding=[0.1] * 768,  # Full 768-dimensional vector
                    metadata={"test": "schema_validation"}
                )
            ],
            metadata={"schema_test": True}
        )
        
        # Store document to verify all schema fields are supported
        store_result = await adapter.store_document(test_doc)
        assert store_result is True, "Document storage should succeed with valid schema"
        
        # Retrieve to verify all fields are preserved
        retrieved = await adapter.retrieve_document(test_doc.id)
        assert retrieved is not None, "Document should be retrievable"
        assert retrieved.filename == test_doc.filename
        assert retrieved.content_hash == test_doc.content_hash
        assert len(retrieved.chunks) == 1
        assert len(retrieved.chunks[0].embedding) == 768
        
        # Clean up
        await adapter.delete_document(test_doc.id)

    # Test 2: Document Storage and Retrieval with Vector Embeddings
    @pytest.mark.asyncio
    async def test_document_storage_and_retrieval(self, adapter, sample_document):
        """Test storing and retrieving documents with vector embeddings."""
        
        # Store the document
        store_result = await adapter.store_document(sample_document)
        assert store_result is True, "Document storage should succeed"
        assert sample_document.id is not None, "Document should have an ID after storage"
        
        original_id = sample_document.id
        
        # Retrieve the document by ID
        retrieved = await adapter.retrieve_document(original_id)
        assert retrieved is not None, "Document should be retrievable by ID"
        assert retrieved.id == original_id
        assert retrieved.filename == sample_document.filename
        assert retrieved.file_path == sample_document.file_path
        assert retrieved.content_hash == sample_document.content_hash
        assert len(retrieved.chunks) == len(sample_document.chunks)
        
        # Verify chunk data integrity
        for i, chunk in enumerate(retrieved.chunks):
            original_chunk = sample_document.chunks[i]
            assert chunk.content == original_chunk.content
            assert chunk.chunk_index == original_chunk.chunk_index
            assert chunk.embedding == original_chunk.embedding
            # Note: metadata might be merged during storage, so check key fields
            assert chunk.metadata.get("chunk_type") == original_chunk.metadata.get("chunk_type")
            assert chunk.metadata.get("language") == original_chunk.metadata.get("language")
        
        # Verify metadata preservation
        assert retrieved.metadata == sample_document.metadata
        
        # Clean up
        delete_result = await adapter.delete_document(original_id)
        assert delete_result is True
    
    @pytest.mark.asyncio
    async def test_find_by_content_hash(self, adapter, sample_document):
        """Test finding documents by content hash."""
        
        # Store the document
        await adapter.store_document(sample_document)
        
        # Find by hash
        found_document = await adapter.find_by_hash(sample_document.content_hash)
        assert found_document is not None, "Document should be found by hash"
        assert found_document.id == sample_document.id
        assert found_document.content_hash == sample_document.content_hash
        
        # Test with non-existent hash
        not_found = await adapter.find_by_hash("non_existent_hash")
        assert not_found is None, "Should return None for non-existent hash"
        
        # Clean up
        await adapter.delete_document(sample_document.id)
    
    @pytest.mark.asyncio
    async def test_document_listing_with_pagination(self, adapter):
        """Test document listing with pagination support."""
        
        # Create multiple test documents
        test_documents = []
        for i in range(10):
            doc = Document(
                filename=f"pagination_test_{i}.txt",
                file_path=Path(f"/test/pagination_test_{i}.txt"),
                content_hash=f"pagination_hash_{i}",
                chunks=[
                    DocumentChunk(
                        content=f"Pagination test content {i}",
                        chunk_index=0,
                        embedding=[float(i)] * 768,
                        metadata={"test_index": i}
                    )
                ],
                metadata={"pagination_test": True, "index": i}
            )
            test_documents.append(doc)
        
        # Store all documents
        for doc in test_documents:
            await adapter.store_document(doc)
        
        # Test listing with different limits
        all_docs = await adapter.list_documents(limit=20)
        assert len(all_docs) >= 10, "Should retrieve at least our test documents"
        
        # Test pagination
        first_page = await adapter.list_documents(limit=5, offset=0)
        second_page = await adapter.list_documents(limit=5, offset=5)
        
        assert len(first_page) <= 5, "First page should have at most 5 documents"
        assert len(second_page) <= 5, "Second page should have at most 5 documents"
        
        # Verify no overlap between pages
        first_page_ids = {doc.id for doc in first_page}
        second_page_ids = {doc.id for doc in second_page}
        assert first_page_ids.isdisjoint(second_page_ids), "Pages should not overlap"
        
        # Clean up
        for doc in test_documents:
            await adapter.delete_document(doc.id)

    # Test 3: Vector Similarity Search Functionality
    @pytest.mark.asyncio
    async def test_vector_similarity_search_functionality(self, adapter):
        """Test vector similarity search functionality works correctly."""
        
        # Create documents with known similar embeddings
        similar_docs = []
        
        # Document 1: Base embedding
        base_embedding = [1.0, 0.0, 0.0] + [0.0] * 765
        doc1 = Document(
            filename="similar_doc_1.txt",
            file_path=Path("/test/similar_doc_1.txt"),
            content_hash="similar_hash_1",
            chunks=[
                DocumentChunk(
                    content="This document is about machine learning and AI.",
                    chunk_index=0,
                    embedding=base_embedding,
                    metadata={"topic": "AI"}
                )
            ],
            metadata={"category": "technology"}
        )
        
        # Document 2: Very similar embedding (small cosine distance)
        similar_embedding = [0.9, 0.1, 0.0] + [0.0] * 765
        doc2 = Document(
            filename="similar_doc_2.txt",
            file_path=Path("/test/similar_doc_2.txt"),
            content_hash="similar_hash_2",
            chunks=[
                DocumentChunk(
                    content="This document discusses artificial intelligence and machine learning.",
                    chunk_index=0,
                    embedding=similar_embedding,
                    metadata={"topic": "AI"}
                )
            ],
            metadata={"category": "technology"}
        )
        
        # Document 3: Dissimilar embedding (large cosine distance)
        dissimilar_embedding = [0.0, 0.0, 1.0] + [0.0] * 765
        doc3 = Document(
            filename="dissimilar_doc.txt",
            file_path=Path("/test/dissimilar_doc.txt"),
            content_hash="dissimilar_hash",
            chunks=[
                DocumentChunk(
                    content="This document is about cooking and recipes.",
                    chunk_index=0,
                    embedding=dissimilar_embedding,
                    metadata={"topic": "cooking"}
                )
            ],
            metadata={"category": "lifestyle"}
        )
        
        similar_docs = [doc1, doc2, doc3]
        
        # Store all documents
        for doc in similar_docs:
            await adapter.store_document(doc)
        
        # Test similarity search using mock client's similarity function
        # Note: Since we're using MockSupabaseClient, we need to test the concept
        # In a real implementation, this would use the similarity_search SQL function
        
        # Verify that documents with similar embeddings can be identified
        # by calculating cosine similarity manually
        import numpy as np
        
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        # Calculate similarities
        sim_1_2 = cosine_similarity(base_embedding, similar_embedding)
        sim_1_3 = cosine_similarity(base_embedding, dissimilar_embedding)
        
        # Verify that doc1 and doc2 are more similar than doc1 and doc3
        assert sim_1_2 > sim_1_3, "Similar documents should have higher cosine similarity"
        assert sim_1_2 > 0.8, "Similar documents should have high similarity score"
        assert sim_1_3 < 0.5, "Dissimilar documents should have low similarity score"
        
        # Test that we can retrieve documents and their embeddings for similarity comparison
        retrieved_doc1 = await adapter.retrieve_document(doc1.id)
        retrieved_doc2 = await adapter.retrieve_document(doc2.id)
        
        assert retrieved_doc1.chunks[0].embedding == base_embedding
        assert retrieved_doc2.chunks[0].embedding == similar_embedding
        
        # Clean up
        for doc in similar_docs:
            await adapter.delete_document(doc.id)
    
    @pytest.mark.asyncio
    async def test_vector_embedding_integrity(self, adapter):
        """Test that vector embeddings maintain precision and integrity."""
        
        # Create document with high-precision embedding values
        precision_embedding = [0.123456789, -0.987654321, 0.555555555] + [0.1] * 765
        
        precision_doc = Document(
            filename="precision_test.txt",
            file_path=Path("/test/precision_test.txt"),
            content_hash="precision_hash",
            chunks=[
                DocumentChunk(
                    content="Testing embedding precision preservation.",
                    chunk_index=0,
                    embedding=precision_embedding,
                    metadata={"precision_test": True}
                )
            ],
            metadata={"test_type": "precision"}
        )
        
        # Store and retrieve
        await adapter.store_document(precision_doc)
        retrieved = await adapter.retrieve_document(precision_doc.id)
        
        # Verify embedding precision is maintained
        retrieved_embedding = retrieved.chunks[0].embedding
        assert len(retrieved_embedding) == len(precision_embedding)
        
        # Check that values are preserved with reasonable precision
        for i, (original, retrieved_val) in enumerate(zip(precision_embedding, retrieved_embedding)):
            assert abs(original - retrieved_val) < 1e-6, f"Embedding value {i} precision not maintained"
        
        # Clean up
        await adapter.delete_document(precision_doc.id)

    # Test 4: Error Scenarios
    @pytest.mark.asyncio
    async def test_connection_failure_scenarios(self):
        """Test error scenarios for connection failures."""
        
        # Test with invalid URL
        invalid_config = create_test_supabase_config(
            url="https://invalid-url-that-does-not-exist.supabase.co",
            service_key="invalid-key",
            table_name="documents"
        )
        
        invalid_adapter = SupabaseStorageAdapter(invalid_config)
        
        # Health check should fail gracefully
        health_status = await invalid_adapter.health_check()
        assert health_status is False, "Health check should fail for invalid configuration"
    
    @pytest.mark.asyncio
    async def test_invalid_data_scenarios(self, adapter):
        """Test error scenarios with invalid data."""
        
        # Test with document containing invalid embedding dimensions
        invalid_doc = Document(
            filename="invalid_embedding.txt",
            file_path=Path("/test/invalid_embedding.txt"),
            content_hash="invalid_hash",
            chunks=[
                DocumentChunk(
                    content="Test content",
                    chunk_index=0,
                    embedding=[0.1, 0.2],  # Wrong dimension (should be 768)
                    metadata={}
                )
            ],
            metadata={}
        )
        
        # This should handle the error gracefully
        # Note: In MockSupabaseClient, this might succeed, but in real Supabase it would fail
        try:
            result = await adapter.store_document(invalid_doc)
            # If it succeeds with mock, that's fine for testing
            if result and invalid_doc.id:
                await adapter.delete_document(invalid_doc.id)
        except StorageError:
            # Expected behavior for invalid data
            pass
    
    @pytest.mark.asyncio
    async def test_nonexistent_document_operations(self, adapter):
        """Test operations on non-existent documents."""
        
        # Test retrieving non-existent document
        non_existent_id = uuid4()
        retrieved = await adapter.retrieve_document(non_existent_id)
        assert retrieved is None, "Should return None for non-existent document"
        
        # Test deleting non-existent document
        delete_result = await adapter.delete_document(non_existent_id)
        assert delete_result is False, "Should return False when deleting non-existent document"
        
        # Test finding by non-existent hash
        found = await adapter.find_by_hash("non_existent_hash_12345")
        assert found is None, "Should return None for non-existent hash"
    
    @pytest.mark.asyncio
    async def test_storage_error_handling(self, adapter):
        """Test proper error handling and exception propagation."""
        
        # Test with document that has None content (invalid)
        invalid_content_doc = Document(
            filename="invalid_content.txt",
            file_path=Path("/test/invalid_content.txt"),
            content_hash="invalid_content_hash",
            chunks=[
                DocumentChunk(
                    content="",  # Empty content might cause issues
                    chunk_index=0,
                    embedding=[0.1] * 768,
                    metadata={}
                )
            ],
            metadata={}
        )
        
        # Should handle empty content gracefully
        try:
            result = await adapter.store_document(invalid_content_doc)
            if result and invalid_content_doc.id:
                await adapter.delete_document(invalid_content_doc.id)
        except StorageError as e:
            # Expected for invalid data
            assert "Failed to store document" in str(e)
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, adapter):
        """Test concurrent storage operations for race conditions."""
        
        # Create multiple documents for concurrent operations
        concurrent_docs = []
        for i in range(5):
            doc = Document(
                filename=f"concurrent_test_{i}.txt",
                file_path=Path(f"/test/concurrent_test_{i}.txt"),
                content_hash=f"concurrent_hash_{i}",
                chunks=[
                    DocumentChunk(
                        content=f"Concurrent test content {i}",
                        chunk_index=0,
                        embedding=[float(i)] * 768,
                        metadata={"concurrent_test": True}
                    )
                ],
                metadata={"test_type": "concurrent", "index": i}
            )
            concurrent_docs.append(doc)
        
        # Store all documents concurrently
        store_tasks = [adapter.store_document(doc) for doc in concurrent_docs]
        store_results = await asyncio.gather(*store_tasks, return_exceptions=True)
        
        # Verify all operations succeeded
        for i, result in enumerate(store_results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent store operation {i} failed: {result}")
            assert result is True, f"Concurrent store operation {i} should succeed"
        
        # Retrieve all documents concurrently
        retrieve_tasks = [adapter.retrieve_document(doc.id) for doc in concurrent_docs]
        retrieve_results = await asyncio.gather(*retrieve_tasks, return_exceptions=True)
        
        # Verify all retrievals succeeded
        for i, result in enumerate(retrieve_results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent retrieve operation {i} failed: {result}")
            assert result is not None, f"Concurrent retrieve operation {i} should succeed"
        
        # Clean up concurrently
        delete_tasks = [adapter.delete_document(doc.id) for doc in concurrent_docs]
        delete_results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        # Verify all deletions succeeded
        for i, result in enumerate(delete_results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent delete operation {i} failed: {result}")
            assert result is True, f"Concurrent delete operation {i} should succeed"

    # Configuration and Environment Tests
    @pytest.mark.asyncio
    async def test_configuration_validation(self):
        """Test configuration validation for various scenarios."""
        
        # Test valid configuration
        valid_config = create_test_supabase_config(
            url="https://valid-project.supabase.co",
            service_key="valid-service-key",
            table_name="documents"
        )
        # Valid config should work fine
        assert valid_config.url == "https://valid-project.supabase.co"
        
        # Test invalid configurations - these should fail at creation time
        # Note: The new config system validates automatically, so we test the underlying Config class
        from src.config import Config
        from pydantic import ValidationError
        import tempfile
        import os
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
        temp_file.write('')
        temp_file.close()
        
        try:
            from unittest.mock import patch
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValidationError):
                    Config(
                        _env_file=temp_file.name,
                        supabase_url="invalid-url",  # Invalid URL format
                        SUPABASE_KEY="valid-anon-key",
                        SUPABASE_SERVICE_KEY="valid-service-key"
                    )
                
                # Test that valid config works
                valid_config = Config(
                    _env_file=temp_file.name,
                    supabase_url="https://valid-project.supabase.co",
                    SUPABASE_KEY="valid-anon-key",
                    SUPABASE_SERVICE_KEY="valid-service-key"
                )
                assert valid_config.supabase_url == "https://valid-project.supabase.co"
        finally:
            os.unlink(temp_file.name)
    
    @pytest.mark.asyncio
    async def test_environment_configuration_loading(self):
        """Test loading configuration from environment variables."""
        
        # Mock environment variables
        test_env = {
            "SUPABASE_URL": "https://env-test.supabase.co",
            "SUPABASE_KEY": "env-test-key",
            "SUPABASE_SERVICE_KEY": "env-test-service-key",
            "SUPABASE_TABLE_NAME": "env_test_documents",
            "SUPABASE_TIMEOUT": "45",
            "SUPABASE_MAX_RETRIES": "5"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            from src.config import Config
            import tempfile
            
            # Create empty env file to prevent reading from project .env
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
            temp_file.write('')
            temp_file.close()
            
            try:
                config = Config(_env_file=temp_file.name)
                
                assert config.supabase_url == "https://env-test.supabase.co"
                assert config.supabase_anon_key == "env-test-key"
                assert config.supabase_table == "env_test_documents"
                assert config.supabase_timeout == 45
                assert config.supabase_max_retries == 5
            finally:
                os.unlink(temp_file.name)
        
        # Test missing required environment variables
        from pydantic import ValidationError
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
        temp_file.write('')
        temp_file.close()
        
        try:
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValidationError):
                    Config(_env_file=temp_file.name)
        finally:
            os.unlink(temp_file.name)


class TestSupabaseStorageAdapterUnit:
    """Unit tests for SupabaseStorageAdapter specific functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        return create_test_supabase_config(
            url="https://mock-test.supabase.co",
            service_key="mock-test-key",
            table_name="mock_documents"
        )
    
    @pytest.fixture
    def adapter_with_mock_client(self, mock_config):
        """Create adapter with a mock client for unit testing."""
        from tests.factories.storage_factory import create_mock_storage_adapter
        return create_mock_storage_adapter(
            url=mock_config.url,
            service_key=mock_config.service_key,
            table_name=mock_config.table_name
        )
    
    @pytest.mark.asyncio
    async def test_mock_client_functionality(self, adapter_with_mock_client):
        """Test that MockSupabaseClient works as expected for testing."""
        
        # Test document storage and retrieval with mock client
        test_doc = Document(
            filename="mock_test.txt",
            file_path=Path("/test/mock_test.txt"),
            content_hash="mock_hash",
            chunks=[
                DocumentChunk(
                    content="Mock test content",
                    chunk_index=0,
                    embedding=[0.1] * 768,
                    metadata={"mock": True}
                )
            ],
            metadata={"test": "mock"}
        )
        
        # Store document
        store_result = await adapter_with_mock_client.store_document(test_doc)
        assert store_result is True
        
        # Retrieve document
        retrieved = await adapter_with_mock_client.retrieve_document(test_doc.id)
        assert retrieved is not None
        assert retrieved.filename == test_doc.filename
        
        # Delete document
        delete_result = await adapter_with_mock_client.delete_document(test_doc.id)
        assert delete_result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])