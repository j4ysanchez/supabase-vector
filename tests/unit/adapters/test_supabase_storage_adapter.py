"""Unit tests for Supabase storage adapter."""

import pytest
from pathlib import Path
from uuid import uuid4

from src.adapters.secondary.supabase.supabase_storage_adapter import SupabaseStorageAdapter
from src.domain.exceptions import StorageError
from src.domain.models.document import Document, DocumentChunk
from src.config import create_test_supabase_config


class TestSupabaseStorageAdapter:
    """Test cases for SupabaseStorageAdapter."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return create_test_supabase_config()
    
    @pytest.fixture
    def adapter(self, config):
        """Create a storage adapter instance with mock client."""
        from tests.factories.storage_factory import create_mock_storage_adapter
        return create_mock_storage_adapter(
            url=config.url,
            service_key=config.service_key,
            table_name=config.table_name
        )
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        chunks = [
            DocumentChunk(
                content="First chunk content",
                chunk_index=0,
                embedding=[0.1, 0.2, 0.3],
                metadata={"type": "text"}
            ),
            DocumentChunk(
                content="Second chunk content",
                chunk_index=1,
                embedding=[0.4, 0.5, 0.6],
                metadata={"type": "text"}
            )
        ]
        
        return Document(
            filename="test.txt",
            file_path=Path("/test/test.txt"),
            content_hash="test_hash_123",
            chunks=chunks,
            metadata={"source": "test"}
        )
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, adapter):
        """Test successful health check."""
        result = await adapter.health_check()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_store_document_success(self, adapter, sample_document):
        """Test successful document storage."""
        result = await adapter.store_document(sample_document)
        assert result is True
        assert sample_document.id is not None
    
    @pytest.mark.asyncio
    async def test_retrieve_document_success(self, adapter, sample_document):
        """Test successful document retrieval."""
        # First store the document
        await adapter.store_document(sample_document)
        
        # Then retrieve it
        retrieved = await adapter.retrieve_document(sample_document.id)
        
        assert retrieved is not None
        assert retrieved.filename == sample_document.filename
        assert retrieved.content_hash == sample_document.content_hash
        assert len(retrieved.chunks) == len(sample_document.chunks)
        
        # Check chunks are in correct order
        for i, chunk in enumerate(retrieved.chunks):
            assert chunk.chunk_index == i
            assert chunk.content == sample_document.chunks[i].content
    
    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_document(self, adapter):
        """Test retrieving a document that doesn't exist."""
        nonexistent_id = uuid4()
        result = await adapter.retrieve_document(nonexistent_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_find_by_hash_success(self, adapter, sample_document):
        """Test finding document by content hash."""
        # First store the document
        await adapter.store_document(sample_document)
        
        # Then find by hash
        found = await adapter.find_by_hash(sample_document.content_hash)
        
        assert found is not None
        assert found.filename == sample_document.filename
        assert found.content_hash == sample_document.content_hash
    
    @pytest.mark.asyncio
    async def test_find_by_nonexistent_hash(self, adapter):
        """Test finding document by non-existent hash."""
        result = await adapter.find_by_hash("nonexistent_hash")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_documents(self, adapter, sample_document):
        """Test listing documents."""
        # Store a document first
        await adapter.store_document(sample_document)
        
        # List documents
        documents = await adapter.list_documents(limit=10)
        
        assert len(documents) >= 1
        assert any(doc.filename == sample_document.filename for doc in documents)
    
    @pytest.mark.asyncio
    async def test_list_documents_empty(self, adapter):
        """Test listing documents when none exist."""
        # Use a fresh adapter with different table name to ensure empty state
        from tests.factories.storage_factory import create_mock_storage_adapter
        empty_adapter = create_mock_storage_adapter(
            url="https://test.supabase.co",
            service_key="test-key",
            table_name="empty_test_table"
        )
        
        documents = await empty_adapter.list_documents()
        assert len(documents) == 0
    
    @pytest.mark.asyncio
    async def test_delete_document_success(self, adapter, sample_document):
        """Test successful document deletion."""
        # First store the document
        await adapter.store_document(sample_document)
        
        # Then delete it
        result = await adapter.delete_document(sample_document.id)
        assert result is True
        
        # Verify it's gone
        retrieved = await adapter.retrieve_document(sample_document.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, adapter):
        """Test deleting a document that doesn't exist."""
        nonexistent_id = uuid4()
        result = await adapter.delete_document(nonexistent_id)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_document_id_generation(self, adapter, sample_document):
        """Test that document ID is generated if not provided."""
        # Ensure document has no ID initially
        sample_document.id = None
        
        # Store the document
        result = await adapter.store_document(sample_document)
        
        assert result is True
        assert sample_document.id is not None
    
    @pytest.mark.asyncio
    async def test_multiple_documents_same_hash(self, adapter):
        """Test handling multiple documents with the same hash."""
        # Create two documents with the same hash
        doc1 = Document(
            filename="doc1.txt",
            file_path=Path("/test/doc1.txt"),
            content_hash="same_hash",
            chunks=[DocumentChunk("content", 0)],
            metadata={}
        )
        
        doc2 = Document(
            filename="doc2.txt",
            file_path=Path("/test/doc2.txt"),
            content_hash="same_hash",
            chunks=[DocumentChunk("content", 0)],
            metadata={}
        )
        
        # Store both documents
        await adapter.store_document(doc1)
        await adapter.store_document(doc2)
        
        # Find by hash should return one of them (implementation dependent)
        found = await adapter.find_by_hash("same_hash")
        assert found is not None
        assert found.content_hash == "same_hash"


if __name__ == "__main__":
    pytest.main([__file__])