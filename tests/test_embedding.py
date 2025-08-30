"""
Test embedding functionality.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx

from vector_db.embedding import EmbeddingClient


@pytest.mark.unit
@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_generate_embedding_success(mock_client_class, embedding_service):
    """Test successful embedding generation."""
    # Setup mock
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    mock_response = Mock()
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    
    text = "Test text for embedding"
    result = await embedding_service.generate_embedding(text)
    
    assert result == [0.1, 0.2, 0.3]
    mock_client.post.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_embedding_http_error():
    """Test embedding generation with HTTP error."""
    service = EmbeddingClient()
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock HTTP error
        mock_client.post.side_effect = httpx.HTTPError("Connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await service.generate_embedding("test text")
        
        assert "Connection failed" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_embedding_invalid_response():
    """Test embedding generation with invalid response."""
    service = EmbeddingClient()
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock invalid response
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid model"}
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
        with pytest.raises(Exception, match="Embedding generation failed"):
            await service.generate_embedding("test text")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_embedding_empty_text(embedding_service):
    """Test embedding generation with empty text."""
    with pytest.raises(ValueError, match="Text cannot be empty"):
        await embedding_service.generate_embedding("")


@pytest.mark.unit
def test_embedding_client_init():
    """Test EmbeddingClient initialization."""
    with patch('vector_db.embedding.config') as mock_config:
        mock_config.ollama_url = "http://test:11434"
        mock_config.ollama_model = "test-model"
        mock_config.max_retries = 3
        
        service = EmbeddingClient()
        
        assert service.base_url == "http://test:11434"
        assert service.model == "test-model"
        assert service.timeout == 60.0  # Default timeout
        assert service.max_retries == 3
        assert service.batch_size == 32  # Default batch size


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_ollama_embedding():
    """Test with real Ollama service (requires Ollama running)."""
    service = EmbeddingClient()
    
    try:
        result = await service.generate_embedding("Hello world")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(x, (int, float)) for x in result)
    except Exception as e:
        pytest.skip(f"Ollama not available: {e}")