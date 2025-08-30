"""Tests for the main VectorDB class."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from vector_db.main import VectorDB
from vector_db.models import Document


class TestVectorDB:
    """Test the main VectorDB class."""
    
    @pytest.fixture
    def vector_db(self):
        """Create a VectorDB instance for testing."""
        return VectorDB()
    
    def test_vector_db_initialization(self, vector_db):
        """Test VectorDB initialization."""
        assert vector_db.config is not None
        assert vector_db.embedding_client is not None
        assert vector_db.storage_client is not None
    
    @pytest.mark.asyncio
    async def test_ingest_file_success(self, mock_vector_db, temp_text_file):
        """Test successful file ingestion."""
        # Mock the embedding generation
        mock_vector_db.embedding_client.generate_embedding.return_value = [0.1] * 768
        
        # Mock storage to return empty list (no existing docs)
        mock_vector_db.storage_client.list_documents.return_value = []
        
        # Mock successful storage
        doc_id = uuid4()
        mock_vector_db.storage_client.store_document.return_value = doc_id
        
        result = await mock_vector_db.ingest_file(temp_text_file)
        
        assert "Successfully ingested" in result
        assert str(doc_id) in result
        mock_vector_db.embedding_client.generate_embedding.assert_called_once()
        mock_vector_db.storage_client.store_document.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ingest_file_not_found(self, mock_vector_db):
        """Test file ingestion with non-existent file."""
        non_existent_file = Path("/non/existent/file.txt")
        
        with pytest.raises(FileNotFoundError):
            await mock_vector_db.ingest_file(non_existent_file)
    
    @pytest.mark.asyncio
    async def test_ingest_file_unsupported_extension(self, mock_vector_db):
        """Test file ingestion with unsupported file extension."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"test content")
            unsupported_file = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                await mock_vector_db.ingest_file(unsupported_file)
        finally:
            unsupported_file.unlink()
    
    @pytest.mark.asyncio
    async def test_ingest_file_duplicate_content(self, mock_vector_db, temp_text_file):
        """Test file ingestion with duplicate content."""
        # Mock existing document with same content hash
        existing_doc = Document(
            filename="existing.txt",
            content="same content",
            id=uuid4(),
            metadata={"content_hash": "some_hash"}
        )
        mock_vector_db.storage_client.list_documents.return_value = [existing_doc]
        
        # Mock the content hash to match
        with patch('hashlib.sha256') as mock_hash:
            mock_hash.return_value.hexdigest.return_value = "some_hash"
            
            result = await mock_vector_db.ingest_file(temp_text_file)
            
            assert "already exists" in result
            # Should not call embedding generation or storage for duplicates
            mock_vector_db.embedding_client.generate_embedding.assert_not_called()
            mock_vector_db.storage_client.store_document.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_ingest_directory_success(self, mock_vector_db, temp_directory):
        """Test successful directory ingestion."""
        # Mock successful ingestion for each file
        mock_vector_db.ingest_file = AsyncMock(return_value="Successfully ingested file")
        
        results = await mock_vector_db.ingest_directory(temp_directory, recursive=False)
        
        assert len(results) > 0
        assert all("Successfully ingested" in result for result in results)
        # Should be called for each supported file
        assert mock_vector_db.ingest_file.call_count > 0
    
    @pytest.mark.asyncio
    async def test_ingest_directory_not_found(self, mock_vector_db):
        """Test directory ingestion with non-existent directory."""
        non_existent_dir = Path("/non/existent/directory")
        
        with pytest.raises(ValueError, match="Directory not found"):
            await mock_vector_db.ingest_directory(non_existent_dir)
    
    @pytest.mark.asyncio
    async def test_ingest_directory_no_supported_files(self, mock_vector_db):
        """Test directory ingestion with no supported files."""
        import tempfile
        import shutil
        
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Create only unsupported files
            (temp_dir / "file.xyz").write_text("unsupported")
            (temp_dir / "file.abc").write_text("also unsupported")
            
            results = await mock_vector_db.ingest_directory(temp_dir)
            
            assert len(results) == 1
            assert "No supported files found" in results[0]
        finally:
            shutil.rmtree(temp_dir)
    
    def test_search_by_text(self, mock_vector_db):
        """Test text search functionality."""
        # Mock search results
        mock_docs = [
            Document(filename="doc1.txt", content="matching content"),
            Document(filename="doc2.txt", content="another match")
        ]
        mock_vector_db.storage_client.search_by_content.return_value = mock_docs
        
        results = mock_vector_db.search_by_text("query", limit=5)
        
        assert len(results) == 2
        assert results[0].filename == "doc1.txt"
        mock_vector_db.storage_client.search_by_content.assert_called_once_with("query", 5)
    
    def test_get_document(self, mock_vector_db):
        """Test document retrieval by ID."""
        doc_id = uuid4()
        mock_doc = Document(filename="test.txt", content="test content", id=doc_id)
        mock_vector_db.storage_client.get_document.return_value = mock_doc
        
        result = mock_vector_db.get_document(doc_id)
        
        assert result == mock_doc
        mock_vector_db.storage_client.get_document.assert_called_once_with(doc_id)
    
    def test_list_documents(self, mock_vector_db):
        """Test document listing."""
        mock_docs = [
            Document(filename="doc1.txt", content="content1"),
            Document(filename="doc2.txt", content="content2")
        ]
        mock_vector_db.storage_client.list_documents.return_value = mock_docs
        
        results = mock_vector_db.list_documents(limit=10, offset=0)
        
        assert len(results) == 2
        mock_vector_db.storage_client.list_documents.assert_called_once_with(10, 0)
    
    def test_delete_document(self, mock_vector_db):
        """Test document deletion."""
        doc_id = uuid4()
        mock_vector_db.storage_client.delete_document.return_value = True
        
        result = mock_vector_db.delete_document(doc_id)
        
        assert result is True
        mock_vector_db.storage_client.delete_document.assert_called_once_with(doc_id)
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, mock_vector_db):
        """Test health check when all services are healthy."""
        mock_vector_db.embedding_client.health_check.return_value = True
        mock_vector_db.storage_client.health_check.return_value = True
        
        status = await mock_vector_db.health_check()
        
        assert status['ollama'] is True
        assert status['supabase'] is True
        assert status['overall'] is True
    
    @pytest.mark.asyncio
    async def test_health_check_partial_failure(self, mock_vector_db):
        """Test health check when some services are down."""
        mock_vector_db.embedding_client.health_check.return_value = True
        mock_vector_db.storage_client.health_check.return_value = False
        
        status = await mock_vector_db.health_check()
        
        assert status['ollama'] is True
        assert status['supabase'] is False
        assert status['overall'] is False
    
    def test_get_stats_success(self, mock_vector_db):
        """Test statistics generation."""
        mock_docs = [
            Document(filename="doc1.txt", content="a" * 100),
            Document(filename="doc2.md", content="b" * 200),
            Document(filename="doc3.txt", content="c" * 150)
        ]
        mock_vector_db.storage_client.list_documents.return_value = mock_docs
        
        stats = mock_vector_db.get_stats()
        
        assert stats['total_documents'] == 3
        assert stats['total_content_size'] == 450
        assert stats['average_document_size'] == 150
        assert stats['file_types']['.txt'] == 2
        assert stats['file_types']['.md'] == 1
        assert 'config' in stats
    
    def test_get_stats_error(self, mock_vector_db):
        """Test statistics generation with error."""
        mock_vector_db.storage_client.list_documents.side_effect = Exception("Database error")
        
        stats = mock_vector_db.get_stats()
        
        assert 'error' in stats
        assert "Database error" in stats['error']