"""Integration tests for storage adapter."""

import pytest
from pathlib import Path

from src.adapters.secondary.supabase.supabase_storage_adapter import SupabaseStorageAdapter
from src.domain.models.document import Document, DocumentChunk
from src.infrastructure.config.supabase_config import SupabaseConfig


class TestStorageIntegration:
    """Integration tests for storage operations."""
    
    @pytest.fixture
    def adapter(self):
        """Create a storage adapter for integration testing."""
        config = SupabaseConfig(
            url="https://integration-test.supabase.co",
            service_key="integration-test-key",
            table_name="integration_test_documents",
            timeout=30,
            max_retries=3
        )
        return SupabaseStorageAdapter(config)
    
    @pytest.mark.asyncio
    async def test_full_document_lifecycle(self, adapter):
        """Test complete document lifecycle: store, retrieve, update, delete."""
        
        # Create a test document
        document = Document(
            filename="lifecycle_test.txt",
            file_path=Path("/test/lifecycle_test.txt"),
            content_hash="lifecycle_hash_123",
            chunks=[
                DocumentChunk(
                    content="Initial content chunk 1",
                    chunk_index=0,
                    embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                    metadata={"version": 1}
                ),
                DocumentChunk(
                    content="Initial content chunk 2",
                    chunk_index=1,
                    embedding=[0.6, 0.7, 0.8, 0.9, 1.0],
                    metadata={"version": 1}
                )
            ],
            metadata={"test": "lifecycle", "version": 1}
        )
        
        # 1. Store the document
        store_result = await adapter.store_document(document)
        assert store_result is True
        assert document.id is not None
        
        original_id = document.id
        
        # 2. Retrieve the document
        retrieved = await adapter.retrieve_document(original_id)
        assert retrieved is not None
        assert retrieved.filename == document.filename
        assert len(retrieved.chunks) == 2
        
        # 3. Find by hash
        found = await adapter.find_by_hash(document.content_hash)
        assert found is not None
        assert found.id == original_id
        
        # 4. List documents (should include our document)
        documents = await adapter.list_documents()
        assert len(documents) >= 1
        assert any(doc.id == original_id for doc in documents)
        
        # 5. Delete the document
        delete_result = await adapter.delete_document(original_id)
        assert delete_result is True
        
        # 6. Verify deletion
        deleted_doc = await adapter.retrieve_document(original_id)
        assert deleted_doc is None
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, adapter):
        """Test batch storage and retrieval operations."""
        
        documents = []
        
        # Create multiple test documents
        for i in range(5):
            doc = Document(
                filename=f"batch_test_{i}.txt",
                file_path=Path(f"/test/batch_test_{i}.txt"),
                content_hash=f"batch_hash_{i}",
                chunks=[
                    DocumentChunk(
                        content=f"Batch content {i} chunk 0",
                        chunk_index=0,
                        embedding=[float(i), float(i+1), float(i+2)],
                        metadata={"batch": i}
                    )
                ],
                metadata={"batch_test": True, "index": i}
            )
            documents.append(doc)
        
        # Store all documents
        stored_ids = []
        for doc in documents:
            result = await adapter.store_document(doc)
            assert result is True
            stored_ids.append(doc.id)
        
        # Retrieve all documents
        for doc_id in stored_ids:
            retrieved = await adapter.retrieve_document(doc_id)
            assert retrieved is not None
        
        # List documents (should include all our documents)
        all_docs = await adapter.list_documents(limit=20)
        stored_filenames = {doc.filename for doc in documents}
        retrieved_filenames = {doc.filename for doc in all_docs}
        
        # All stored documents should be in the retrieved list
        assert stored_filenames.issubset(retrieved_filenames)
        
        # Clean up - delete all test documents
        for doc_id in stored_ids:
            delete_result = await adapter.delete_document(doc_id)
            assert delete_result is True
    
    @pytest.mark.asyncio
    async def test_large_document_handling(self, adapter):
        """Test handling of documents with many chunks."""
        
        # Create a document with many chunks
        chunks = []
        for i in range(50):  # 50 chunks
            chunk = DocumentChunk(
                content=f"Large document chunk {i} with some content to make it realistic. " * 10,
                chunk_index=i,
                embedding=[float(j) for j in range(768)],  # Realistic embedding size
                metadata={"chunk_size": "large", "position": i}
            )
            chunks.append(chunk)
        
        large_document = Document(
            filename="large_test_document.txt",
            file_path=Path("/test/large_test_document.txt"),
            content_hash="large_document_hash",
            chunks=chunks,
            metadata={"size": "large", "chunk_count": len(chunks)}
        )
        
        # Store the large document
        store_result = await adapter.store_document(large_document)
        assert store_result is True
        
        # Retrieve and verify
        retrieved = await adapter.retrieve_document(large_document.id)
        assert retrieved is not None
        assert len(retrieved.chunks) == 50
        
        # Verify chunks are in correct order
        for i, chunk in enumerate(retrieved.chunks):
            assert chunk.chunk_index == i
            assert f"chunk {i}" in chunk.content
        
        # Clean up
        delete_result = await adapter.delete_document(large_document.id)
        assert delete_result is True


if __name__ == "__main__":
    pytest.main([__file__])