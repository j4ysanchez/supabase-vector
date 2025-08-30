"""
Test storage functionality.
"""
import pytest
import datetime
from unittest.mock import Mock, patch
from uuid import UUID

from vector_db.storage import StorageClient
from vector_db.models import Document


@pytest.mark.unit
def test_store_document_success(storage_service):
    """Test successful document storage."""
    doc = Document(
        filename="test.txt",
        content="Test content",
        embedding=[0.1, 0.2, 0.3],
        metadata={"source": "test"}
    )
    
    result = storage_service.store_document(doc)
    
    assert result is not None
    storage_service._client.table.assert_called_with("documents")
    storage_service._client.table().insert.assert_called_once()


@pytest.mark.unit
def test_store_document_client_error(storage_service):
    """Test document storage with client error."""
    # Mock client error
    storage_service._client.table().insert().execute.side_effect = Exception("Database error")
    
    doc = Document(
        filename="test.txt",
        content="Test content",
        embedding=[0.1, 0.2, 0.3]
    )
    
    with pytest.raises(Exception) as exc_info:
        storage_service.store_document(doc)
    
    assert "Database error" in str(exc_info.value)


@pytest.mark.unit
def test_search_documents_success(storage_service):
    """Test successful document search."""
    # Use the default mock data from conftest.py which has proper UUID
    results = storage_service.search_by_content("test query", limit=5)
    
    assert len(results) == 1
    assert results[0].filename == "test.txt"


@pytest.mark.unit
def test_search_documents_empty_results(storage_service):
    """Test document search with no results."""
    # Mock empty results
    storage_service._client.table().select().execute.return_value.data = []
    
    results = storage_service.search_by_content("nonexistent query", limit=5)
    
    assert len(results) == 0


@pytest.mark.unit
def test_list_documents(storage_service):
    """Test listing documents."""
    # Mock document results
    storage_service._client.table().select().range().order().execute.return_value.data = [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "test.txt",
            "content": "Test content",
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {},
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
    
    results = storage_service.list_documents(limit=10)
    
    assert len(results) == 1
    assert results[0].filename == "test.txt"


@pytest.mark.unit
def test_health_check_success(storage_service):
    """Test successful health check."""
    # Mock successful health check
    storage_service._client.table().select().limit().execute.return_value = Mock()
    
    result = storage_service.health_check()
    
    assert result is True


@pytest.mark.unit
def test_health_check_failure(storage_service):
    """Test failed health check."""
    # Mock failed health check
    storage_service._client.table().select().limit().execute.side_effect = Exception("Connection failed")
    
    result = storage_service.health_check()
    
    assert result is False


@pytest.mark.unit
def test_storage_client_init():
    """Test StorageClient initialization."""
    with patch('vector_db.storage.config') as mock_config:
        mock_config.supabase_url = "https://test.supabase.co"
        mock_config.supabase_key = "test-key"
        mock_config.supabase_table = "test_documents"
        mock_config.max_retries = 3
        
        service = StorageClient()
        
        assert service.url == "https://test.supabase.co"
        assert service.key == "test-key"
        assert service.table == "test_documents"
        assert service.timeout == 30.0  # Default timeout
        assert service.max_retries == 3


@pytest.mark.integration
def test_real_supabase_connection():
    """Test with real Supabase connection (requires valid credentials)."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Skip if no real credentials
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
        pytest.skip("No Supabase credentials provided")
    
    try:
        service = StorageClient()
        # Just test connection, don't modify data
        result = service.health_check()
        assert isinstance(result, bool)
    except Exception as e:
        pytest.skip(f"Supabase not available: {e}")


@pytest.mark.integration
def test_env_variables_loaded():
    """Test that environment variables are properly loaded from .env file."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Check that key environment variables are loaded
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if supabase_url and supabase_key:
        # Verify the format of the loaded variables
        assert supabase_url.startswith('https://'), "SUPABASE_URL should start with https://"
        assert supabase_url.endswith('.supabase.co'), "SUPABASE_URL should end with .supabase.co"
        assert len(supabase_key) > 100, "SUPABASE_KEY should be a JWT token (long string)"
        
        # Test that StorageClient can use these variables
        service = StorageClient()
        assert service.url == supabase_url
        assert service.key == supabase_key
    else:
        pytest.skip("Supabase environment variables not found in .env file")