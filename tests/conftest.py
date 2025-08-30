"""
Simplified test configuration and fixtures.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import httpx

from src.config import Config
from vector_db.storage import StorageClient
from vector_db.embedding import EmbeddingClient


@pytest.fixture
def test_config():
    """Test configuration with safe defaults."""
    from vector_db.config import Config as VectorConfig
    return VectorConfig(
        _env_file=None,  # Don't load .env file for tests
        supabase_url="https://test.supabase.co",
        supabase_key="test-anon-key",
        supabase_table="test_documents",
        ollama_url="http://localhost:11434",
        ollama_model="nomic-embed-text",
        chunk_size=100,
        chunk_overlap=20
    )


@pytest.fixture
def temp_file():
    """Create a temporary test file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is test content for embedding.")
        temp_path = f.name
    
    yield Path(temp_path)
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = Mock()
    mock_table = Mock()
    mock_client.table.return_value = mock_table
    
    # Create a flexible mock result that can be modified by tests
    mock_result = Mock()
    mock_result.data = [{"id": "123e4567-e89b-12d3-a456-426614174000", "filename": "test.txt", "content": "Test content", "embedding": [0.1, 0.2, 0.3], "metadata": {}, "created_at": "2024-01-01T00:00:00Z"}]
    
    # Create mock chain objects that can be modified
    mock_select = Mock()
    mock_ilike = Mock()
    mock_limit = Mock()
    mock_eq = Mock()
    mock_range = Mock()
    mock_order = Mock()
    mock_insert = Mock()
    mock_delete = Mock()
    
    # Set up the chain
    mock_table.select.return_value = mock_select
    mock_table.insert.return_value = mock_insert
    mock_table.delete.return_value = mock_delete
    
    # Select chains
    mock_select.execute.return_value = mock_result
    mock_select.eq.return_value = mock_eq
    mock_select.ilike.return_value = mock_ilike
    mock_select.range.return_value = mock_range
    mock_select.limit.return_value = mock_limit
    
    # Other chains
    mock_eq.execute.return_value = mock_result
    mock_ilike.limit.return_value = mock_limit
    mock_limit.execute.return_value = mock_result
    mock_range.order.return_value = mock_order
    mock_order.execute.return_value = mock_result
    mock_insert.execute.return_value = mock_result
    mock_delete.eq.return_value = mock_eq
    
    return mock_client


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama HTTP client for testing."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    
    # Mock successful embedding response
    mock_response = Mock()
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    
    return mock_client


@pytest.fixture
def storage_service(test_config, mock_supabase_client):
    """Storage service with mocked client."""
    with patch('vector_db.storage.get_config', return_value=test_config):
        service = StorageClient()
        service._client = mock_supabase_client
        # Ensure the service has the test config values
        service.url = test_config.supabase_url
        service.key = test_config.supabase_key
        service.table = test_config.supabase_table
        service.timeout = 30.0
        service.max_retries = test_config.max_retries
        return service


@pytest.fixture
def embedding_service(test_config):
    """Embedding service for testing."""
    return EmbeddingClient()


# Pytest markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "live: Live tests requiring real services")