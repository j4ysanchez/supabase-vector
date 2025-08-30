"""
Test main application logic.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from vector_db.main import VectorDB
from vector_db.models import Document


@pytest.mark.unit
@patch('vector_db.main.StorageClient')
@patch('vector_db.main.EmbeddingClient')
@patch('vector_db.main.config')
def test_vector_db_init(mock_config, mock_embedding, mock_storage):
    """Test VectorDB initialization."""
    mock_config.setup_logging = Mock()
    
    db = VectorDB()
    
    assert db.config == mock_config
    mock_storage.assert_called_once()
    mock_embedding.assert_called_once()
    mock_config.setup_logging.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_file_success():
    """Test successful file ingestion."""
    with patch('vector_db.main.StorageClient') as mock_storage, \
         patch('vector_db.main.EmbeddingClient') as mock_embedding, \
         patch('vector_db.main.get_config') as mock_get_config:
        
        # Mock config
        mock_config = Mock()
        mock_config.max_file_size_bytes = 1024 * 1024
        mock_config.extensions_list = ('.txt',)
        mock_config.setup_logging = Mock()
        mock_get_config.return_value = mock_config
        
        # Mock services
        mock_storage_instance = Mock()
        mock_embedding_instance = AsyncMock()
        mock_storage.return_value = mock_storage_instance
        mock_embedding.return_value = mock_embedding_instance
        
        # Mock embedding generation
        mock_embedding_instance.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Mock storage
        mock_storage_instance.list_documents.return_value = []  # No existing docs
        mock_storage_instance.store_document.return_value = "doc-id-123"
        
        db = VectorDB()
        
        # Create test file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document content")
            temp_path = Path(f.name)
        
        try:
            result = await db.ingest_file(temp_path)
            
            assert "Successfully ingested" in result
            assert "doc-id-123" in result
            mock_embedding_instance.generate_embedding.assert_called_once()
            mock_storage_instance.store_document.assert_called_once()
        finally:
            temp_path.unlink()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_file_not_found():
    """Test ingesting non-existent file."""
    with patch('vector_db.main.StorageClient'), \
         patch('vector_db.main.EmbeddingClient'), \
         patch('vector_db.main.get_config') as mock_get_config:
        
        mock_config = Mock()
        mock_config.setup_logging = Mock()
        mock_get_config.return_value = mock_config
        
        db = VectorDB()
        
        with pytest.raises(FileNotFoundError):
            await db.ingest_file(Path("nonexistent.txt"))


@pytest.mark.unit
def test_search_by_text():
    """Test text search functionality."""
    with patch('vector_db.main.StorageClient') as mock_storage, \
         patch('vector_db.main.EmbeddingClient'), \
         patch('vector_db.main.get_config') as mock_get_config:
        
        # Mock config
        mock_config = Mock()
        mock_config.setup_logging = Mock()
        mock_get_config.return_value = mock_config
        
        # Mock storage
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        
        from vector_db.models import Document
        mock_doc = Document(filename="test.txt", content="Test content")
        mock_storage_instance.search_by_content.return_value = [mock_doc]
        
        db = VectorDB()
        results = db.search_by_text("test query", limit=5)
        
        assert len(results) == 1
        assert results[0].filename == "test.txt"
        mock_storage_instance.search_by_content.assert_called_once_with("test query", 5)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check():
    """Test health check functionality."""
    with patch('vector_db.main.StorageClient') as mock_storage, \
         patch('vector_db.main.EmbeddingClient') as mock_embedding, \
         patch('vector_db.main.get_config') as mock_get_config:
        
        # Mock config
        mock_config = Mock()
        mock_config.setup_logging = Mock()
        mock_get_config.return_value = mock_config
        
        # Mock services
        mock_storage_instance = Mock()
        mock_embedding_instance = AsyncMock()
        mock_storage.return_value = mock_storage_instance
        mock_embedding.return_value = mock_embedding_instance
        
        # Mock health checks
        mock_storage_instance.health_check.return_value = True
        mock_embedding_instance.health_check.return_value = True
        
        db = VectorDB()
        status = await db.health_check()
        
        assert status['supabase'] is True
        assert status['ollama'] is True
        assert status['overall'] is True


@pytest.mark.unit
def test_list_documents():
    """Test listing documents."""
    with patch('vector_db.main.StorageClient') as mock_storage, \
         patch('vector_db.main.EmbeddingClient'), \
         patch('vector_db.main.get_config') as mock_get_config:
        
        # Mock config
        mock_config = Mock()
        mock_config.setup_logging = Mock()
        mock_get_config.return_value = mock_config
        
        # Mock storage
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        
        from vector_db.models import Document
        mock_docs = [Document(filename="test1.txt", content="Content 1"),
                    Document(filename="test2.txt", content="Content 2")]
        mock_storage_instance.list_documents.return_value = mock_docs
        
        db = VectorDB()
        results = db.list_documents(limit=10, offset=0)
        
        assert len(results) == 2
        assert results[0].filename == "test1.txt"
        mock_storage_instance.list_documents.assert_called_once_with(10, 0)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow():
    """Integration test of full ingest and search workflow."""
    # This would test the complete workflow with real services
    # Skip if services not available
    pytest.skip("Integration test - requires running services")