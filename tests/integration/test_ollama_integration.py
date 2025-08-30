"""Integration tests for Ollama embedding adapter."""

import pytest
import httpx
from unittest.mock import Mock

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
        max_retries=1,
        batch_size=2
    )


class TestOllamaIntegration:
    """Integration tests for OllamaEmbeddingAdapter."""
    
    @pytest.mark.asyncio
    async def test_embedding_adapter_initialization(self, ollama_config):
        """Test that the adapter can be initialized properly."""
        # Act
        async with OllamaEmbeddingAdapter(ollama_config) as adapter:
            # Assert
            assert adapter.get_embedding_dimension() == 768
            assert adapter._config.model_name == "nomic-embed-text"
            assert adapter._config.base_url == "http://localhost:11434"
    
    @pytest.mark.asyncio
    async def test_embedding_generation_with_mock_server(self, ollama_config):
        """Test embedding generation with a mocked HTTP response."""
        # Arrange
        test_texts = ["Hello world", "This is a test"]
        expected_embeddings = [
            [0.1] * 768,
            [0.2] * 768
        ]
        
        # Create a mock client that simulates successful responses
        mock_client = httpx.AsyncClient()
        
        # Mock the post method to return successful responses
        original_post = mock_client.post
        
        async def mock_post(url, **kwargs):
            # Create a mock response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            # Return different embeddings based on the prompt
            prompt = kwargs.get("json", {}).get("prompt", "")
            if "Hello world" in prompt:
                mock_response.json.return_value = {"embedding": expected_embeddings[0]}
            elif "This is a test" in prompt:
                mock_response.json.return_value = {"embedding": expected_embeddings[1]}
            else:
                mock_response.json.return_value = {"embedding": [0.0] * 768}
            
            return mock_response
        
        mock_client.post = mock_post
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            embeddings = await adapter.generate_embeddings(test_texts)
        
        # Assert
        assert len(embeddings) == 2
        assert embeddings[0] == expected_embeddings[0]
        assert embeddings[1] == expected_embeddings[1]
    
    @pytest.mark.asyncio
    async def test_health_check_with_mock_server(self, ollama_config):
        """Test health check with a mocked HTTP response."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_get(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "models": [
                    {"name": "nomic-embed-text"},
                    {"name": "other-model"}
                ]
            }
            return mock_response
        
        mock_client.get = mock_get
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            is_healthy = await adapter.health_check()
        
        # Assert
        assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, ollama_config):
        """Test that batch processing works correctly."""
        # Arrange
        test_texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]  # More than batch_size
        
        mock_client = httpx.AsyncClient()
        call_count = 0
        
        async def mock_post(url, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"embedding": [0.1 * call_count] * 768}
            return mock_response
        
        mock_client.post = mock_post
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            embeddings = await adapter.generate_embeddings(test_texts)
        
        # Assert
        assert len(embeddings) == 5
        assert call_count == 5  # Each text should result in one API call
        
        # Verify embeddings are different (based on our mock)
        for i, embedding in enumerate(embeddings):
            expected_value = 0.1 * (i + 1)
            assert embedding[0] == expected_value
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, ollama_config):
        """Test error handling in an integration context."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_post(url, **kwargs):
            raise httpx.RequestError("Connection failed")
        
        mock_client.post = mock_post
        
        # Act & Assert
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            with pytest.raises(EmbeddingError) as exc_info:
                await adapter.generate_embedding("Test text")
            
            assert "Failed to connect to Ollama" in str(exc_info.value)
            assert exc_info.value.original_error is not None