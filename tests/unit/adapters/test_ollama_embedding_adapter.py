"""Unit tests for OllamaEmbeddingAdapter."""

import pytest
from unittest.mock import AsyncMock, Mock
import httpx

from src.adapters.secondary.ollama.ollama_embedding_adapter import OllamaEmbeddingAdapter
from src.infrastructure.config.ollama_config import OllamaConfig
from src.domain.exceptions import EmbeddingError


@pytest.fixture
def ollama_config():
    """Create a test Ollama configuration."""
    return OllamaConfig(
        base_url="http://localhost:11434",
        model_name="nomic-embed-text",
        timeout=30,
        max_retries=2,
        batch_size=2
    )


@pytest.fixture
def mock_client():
    """Create a mock httpx client."""
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def adapter(ollama_config, mock_client):
    """Create an OllamaEmbeddingAdapter with mocked client."""
    return OllamaEmbeddingAdapter(ollama_config, mock_client)


class TestOllamaEmbeddingAdapter:
    """Test cases for OllamaEmbeddingAdapter."""
    
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, adapter, mock_client):
        """Test successful single embedding generation."""
        # Arrange
        test_text = "Hello world"
        expected_embedding = [0.1, 0.2, 0.3] * 256  # 768 dimensions
        
        mock_response = Mock()
        mock_response.json.return_value = {"embedding": expected_embedding}
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
        # Act
        result = await adapter.generate_embedding(test_text)
        
        # Assert
        assert result == expected_embedding
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/embeddings"
        assert call_args[1]["json"]["model"] == "nomic-embed-text"
        assert call_args[1]["json"]["prompt"] == test_text
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, adapter, mock_client):
        """Test batch embedding generation."""
        # Arrange
        test_texts = ["Hello", "World", "Test"]
        expected_embeddings = [
            [0.1] * 768,
            [0.2] * 768,
            [0.3] * 768
        ]
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
        # Mock responses for each text
        mock_response.json.side_effect = [
            {"embedding": expected_embeddings[0]},
            {"embedding": expected_embeddings[1]},
            {"embedding": expected_embeddings[2]}
        ]
        
        # Act
        result = await adapter.generate_embeddings(test_texts)
        
        # Assert
        assert len(result) == 3
        assert result == expected_embeddings
        assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_empty_list(self, adapter):
        """Test embedding generation with empty input."""
        # Act
        result = await adapter.generate_embeddings([])
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_generate_embedding_http_error(self, adapter, mock_client):
        """Test handling of HTTP errors."""
        # Arrange
        test_text = "Hello world"
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )
        
        # Act & Assert
        with pytest.raises(EmbeddingError) as exc_info:
            await adapter.generate_embedding(test_text)
        
        assert "HTTP error 500" in str(exc_info.value)
        assert "Internal Server Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_network_error(self, adapter, mock_client):
        """Test handling of network errors."""
        # Arrange
        test_text = "Hello world"
        mock_client.post.side_effect = httpx.RequestError("Connection failed")
        
        # Act & Assert
        with pytest.raises(EmbeddingError) as exc_info:
            await adapter.generate_embedding(test_text)
        
        assert "Failed to connect to Ollama" in str(exc_info.value)
        assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_invalid_response(self, adapter, mock_client):
        """Test handling of invalid response format."""
        # Arrange
        test_text = "Hello world"
        
        mock_response = Mock()
        mock_response.json.return_value = {"invalid": "response"}
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(EmbeddingError) as exc_info:
            await adapter.generate_embedding(test_text)
        
        assert "missing 'embedding' field" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_retry_logic(self, adapter, mock_client):
        """Test retry logic on failures."""
        # Arrange
        test_text = "Hello world"
        expected_embedding = [0.1] * 768
        
        # First two calls fail, third succeeds
        mock_client.post.side_effect = [
            httpx.RequestError("Connection failed"),
            httpx.RequestError("Connection failed"),
            Mock(json=lambda: {"embedding": expected_embedding}, raise_for_status=lambda: None)
        ]
        
        # Act
        result = await adapter.generate_embedding(test_text)
        
        # Assert
        assert result == expected_embedding
        assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_generate_embedding_max_retries_exceeded(self, adapter, mock_client):
        """Test behavior when max retries are exceeded."""
        # Arrange
        test_text = "Hello world"
        mock_client.post.side_effect = httpx.RequestError("Connection failed")
        
        # Act & Assert
        with pytest.raises(EmbeddingError) as exc_info:
            await adapter.generate_embedding(test_text)
        
        assert "Failed to generate embeddings after 3 attempts" in str(exc_info.value)
        assert mock_client.post.call_count == 3  # max_retries + 1
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, adapter, mock_client):
        """Test successful health check."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "nomic-embed-text"},
                {"name": "other-model"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response
        
        # Act
        result = await adapter.health_check()
        
        # Assert
        assert result is True
        mock_client.get.assert_called_once_with("http://localhost:11434/api/tags")
    
    @pytest.mark.asyncio
    async def test_health_check_model_not_available(self, adapter, mock_client):
        """Test health check when model is not available."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "other-model"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response
        
        # Act
        result = await adapter.health_check()
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_connection_error(self, adapter, mock_client):
        """Test health check with connection error."""
        # Arrange
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        
        # Act
        result = await adapter.health_check()
        
        # Assert
        assert result is False
    
    def test_get_embedding_dimension(self, adapter):
        """Test getting embedding dimension."""
        # Act
        dimension = adapter.get_embedding_dimension()
        
        # Assert
        assert dimension == 768
    
    @pytest.mark.asyncio
    async def test_context_manager(self, ollama_config):
        """Test async context manager functionality."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            assert adapter is not None
        
        # Assert
        mock_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close(self, adapter, mock_client):
        """Test explicit close method."""
        # Act
        await adapter.close()
        
        # Assert
        mock_client.aclose.assert_called_once()