"""Integration tests for Ollama embedding adapter."""

import pytest
import httpx
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import List, Dict, Any

from src.adapters.secondary.ollama.ollama_embedding_adapter import OllamaEmbeddingAdapter
from src.infrastructure.config.ollama_config import OllamaConfig
from src.infrastructure.config.config_validation import ConfigValidationError
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


@pytest.fixture
def ollama_config_with_retries():
    """Create a test Ollama configuration with multiple retries."""
    return OllamaConfig(
        base_url="http://localhost:11434",
        model_name="nomic-embed-text",
        timeout=30,
        max_retries=3,
        batch_size=5
    )


class TestOllamaServiceConnection:
    """Test connection to Ollama service and model availability."""
    
    @pytest.mark.asyncio
    async def test_service_connection_and_model_availability(self, ollama_config):
        """Test connection to Ollama service and verify model availability."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_get(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "models": [
                    {"name": "nomic-embed-text", "size": 274301056},
                    {"name": "llama2", "size": 3825819519},
                    {"name": "mistral", "size": 4109856768}
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
    async def test_service_connection_model_not_available(self, ollama_config):
        """Test health check when required model is not available."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_get(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "size": 3825819519},
                    {"name": "mistral", "size": 4109856768}
                ]
            }
            return mock_response
        
        mock_client.get = mock_get
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            is_healthy = await adapter.health_check()
        
        # Assert
        assert is_healthy is False
    
    @pytest.mark.asyncio
    async def test_service_connection_failure(self, ollama_config):
        """Test health check when service is unavailable."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_get(url, **kwargs):
            raise httpx.ConnectError("Connection refused")
        
        mock_client.get = mock_get
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            is_healthy = await adapter.health_check()
        
        # Assert
        assert is_healthy is False
    
    @pytest.mark.asyncio
    async def test_service_http_error_response(self, ollama_config):
        """Test health check with HTTP error responses."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_get(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=Mock(status_code=404)
            )
            return mock_response
        
        mock_client.get = mock_get
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            is_healthy = await adapter.health_check()
        
        # Assert
        assert is_healthy is False


class TestEmbeddingGeneration:
    """Test embedding generation and vector dimensions."""
    
    @pytest.mark.asyncio
    async def test_single_text_embedding_generation(self, ollama_config):
        """Test embedding generation for a single text produces expected dimensions."""
        # Arrange
        test_text = "This is a test document for embedding generation."
        expected_embedding = [0.1] * 768  # nomic-embed-text produces 768-dimensional embeddings
        
        mock_client = httpx.AsyncClient()
        
        async def mock_post(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"embedding": expected_embedding}
            return mock_response
        
        mock_client.post = mock_post
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            embedding = await adapter.generate_embedding(test_text)
        
        # Assert
        assert len(embedding) == 768
        assert embedding == expected_embedding
        assert adapter.get_embedding_dimension() == 768
    
    @pytest.mark.asyncio
    async def test_multiple_text_embedding_generation(self, ollama_config):
        """Test embedding generation for multiple texts produces correct dimensions."""
        # Arrange
        test_texts = [
            "First document about machine learning.",
            "Second document about natural language processing.",
            "Third document about vector databases."
        ]
        expected_embeddings = [
            [0.1] * 768,
            [0.2] * 768,
            [0.3] * 768
        ]
        
        mock_client = httpx.AsyncClient()
        call_count = 0
        
        async def mock_post(url, **kwargs):
            nonlocal call_count
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"embedding": expected_embeddings[call_count]}
            call_count += 1
            return mock_response
        
        mock_client.post = mock_post
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            embeddings = await adapter.generate_embeddings(test_texts)
        
        # Assert
        assert len(embeddings) == 3
        for i, embedding in enumerate(embeddings):
            assert len(embedding) == 768
            assert embedding == expected_embeddings[i]
    
    @pytest.mark.asyncio
    async def test_empty_text_list_handling(self, ollama_config):
        """Test handling of empty text list."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            embeddings = await adapter.generate_embeddings([])
        
        # Assert
        assert embeddings == []
    
    @pytest.mark.asyncio
    async def test_unexpected_embedding_dimension(self, ollama_config):
        """Test handling of unexpected embedding dimensions."""
        # Arrange
        test_text = "Test text"
        unexpected_embedding = [0.1] * 512  # Different dimension than expected
        
        mock_client = httpx.AsyncClient()
        
        async def mock_post(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"embedding": unexpected_embedding}
            return mock_response
        
        mock_client.post = mock_post
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            embedding = await adapter.generate_embedding(test_text)
        
        # Assert
        assert len(embedding) == 512
        assert adapter.get_embedding_dimension() == 512  # Should adapt to actual dimension


class TestBatchProcessing:
    """Test batch processing for multiple text inputs."""
    
    @pytest.mark.asyncio
    async def test_batch_processing_within_limit(self, ollama_config):
        """Test batch processing when all texts fit within batch size."""
        # Arrange - batch_size is 2 in ollama_config
        test_texts = ["Text 1", "Text 2"]
        expected_embeddings = [[0.1] * 768, [0.2] * 768]
        
        mock_client = httpx.AsyncClient()
        call_count = 0
        
        async def mock_post(url, **kwargs):
            nonlocal call_count
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"embedding": expected_embeddings[call_count]}
            call_count += 1
            return mock_response
        
        mock_client.post = mock_post
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            embeddings = await adapter.generate_embeddings(test_texts)
        
        # Assert
        assert len(embeddings) == 2
        assert call_count == 2  # Each text processed individually
        assert embeddings == expected_embeddings
    
    @pytest.mark.asyncio
    async def test_batch_processing_exceeds_limit(self, ollama_config):
        """Test batch processing when texts exceed batch size."""
        # Arrange - batch_size is 2, so 5 texts should be processed in batches
        test_texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
        expected_embeddings = [
            [0.1] * 768, [0.2] * 768, [0.3] * 768, [0.4] * 768, [0.5] * 768
        ]
        
        mock_client = httpx.AsyncClient()
        call_count = 0
        
        async def mock_post(url, **kwargs):
            nonlocal call_count
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"embedding": expected_embeddings[call_count]}
            call_count += 1
            return mock_response
        
        mock_client.post = mock_post
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            embeddings = await adapter.generate_embeddings(test_texts)
        
        # Assert
        assert len(embeddings) == 5
        assert call_count == 5  # Each text processed individually
        assert embeddings == expected_embeddings
    
    @pytest.mark.asyncio
    async def test_large_batch_processing(self, ollama_config_with_retries):
        """Test processing of large batches efficiently."""
        # Arrange - Create a larger batch to test efficiency
        test_texts = [f"Document {i} content for testing batch processing." for i in range(20)]
        
        mock_client = httpx.AsyncClient()
        call_count = 0
        
        async def mock_post(url, **kwargs):
            nonlocal call_count
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            # Create unique embedding for each call
            embedding = [0.1 * (call_count + 1)] * 768
            mock_response.json.return_value = {"embedding": embedding}
            call_count += 1
            return mock_response
        
        mock_client.post = mock_post
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config_with_retries, mock_client) as adapter:
            embeddings = await adapter.generate_embeddings(test_texts)
        
        # Assert
        assert len(embeddings) == 20
        assert call_count == 20
        
        # Verify each embedding is unique
        for i, embedding in enumerate(embeddings):
            expected_value = 0.1 * (i + 1)
            assert embedding[0] == expected_value
            assert len(embedding) == 768


class TestErrorScenarios:
    """Test error scenarios including service unavailable and invalid model."""
    
    @pytest.mark.asyncio
    async def test_service_unavailable_error(self, ollama_config):
        """Test handling when Ollama service is unavailable."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_post(url, **kwargs):
            raise httpx.ConnectError("Connection refused")
        
        mock_client.post = mock_post
        
        # Act & Assert
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            with pytest.raises(EmbeddingError) as exc_info:
                await adapter.generate_embedding("Test text")
            
            # The error message should indicate connection failure after retries
            assert "Failed to generate embeddings after" in str(exc_info.value)
            assert "Failed to connect to Ollama" in str(exc_info.value)
            assert exc_info.value.original_error is not None
            # The original error is wrapped in another EmbeddingError due to retry mechanism
            assert isinstance(exc_info.value.original_error, EmbeddingError)
    
    @pytest.mark.asyncio
    async def test_http_error_responses(self, ollama_config):
        """Test handling of various HTTP error responses."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_post(url, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Model not found"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=mock_response
            )
            return mock_response
        
        mock_client.post = mock_post
        
        # Act & Assert
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            with pytest.raises(EmbeddingError) as exc_info:
                await adapter.generate_embedding("Test text")
            
            assert "Ollama API request failed" in str(exc_info.value)
            assert "404" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_response_format(self, ollama_config):
        """Test handling of invalid response format from Ollama."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_post(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"error": "Invalid request"}  # Missing 'embedding' field
            return mock_response
        
        mock_client.post = mock_post
        
        # Act & Assert
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            with pytest.raises(EmbeddingError) as exc_info:
                await adapter.generate_embedding("Test text")
            
            assert "Invalid response format" in str(exc_info.value)
            assert "missing 'embedding' field" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_embedding_format(self, ollama_config):
        """Test handling of invalid embedding format in response."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_post(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"embedding": "not_a_list"}  # Invalid format
            return mock_response
        
        mock_client.post = mock_post
        
        # Act & Assert
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            with pytest.raises(EmbeddingError) as exc_info:
                await adapter.generate_embedding("Test text")
            
            assert "Invalid embedding format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_empty_embedding_response(self, ollama_config):
        """Test handling of empty embedding in response."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_post(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"embedding": []}  # Empty embedding
            return mock_response
        
        mock_client.post = mock_post
        
        # Act & Assert
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            with pytest.raises(EmbeddingError) as exc_info:
                await adapter.generate_embedding("Test text")
            
            assert "Invalid embedding format" in str(exc_info.value)
            assert "expected non-empty list" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_with_transient_errors(self, ollama_config_with_retries):
        """Test retry mechanism with transient network errors."""
        # Arrange
        mock_client = httpx.AsyncClient()
        attempt_count = 0
        
        async def mock_post(url, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < 3:  # Fail first 2 attempts
                raise httpx.RequestError("Temporary network error")
            else:  # Succeed on 3rd attempt
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = {"embedding": [0.1] * 768}
                return mock_response
        
        mock_client.post = mock_post
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config_with_retries, mock_client) as adapter:
            embedding = await adapter.generate_embedding("Test text")
        
        # Assert
        assert len(embedding) == 768
        assert attempt_count == 3  # Should have retried twice before succeeding
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, ollama_config_with_retries):
        """Test behavior when all retry attempts are exhausted."""
        # Arrange
        mock_client = httpx.AsyncClient()
        attempt_count = 0
        
        async def mock_post(url, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            raise httpx.RequestError("Persistent network error")
        
        mock_client.post = mock_post
        
        # Act & Assert
        async with OllamaEmbeddingAdapter(ollama_config_with_retries, mock_client) as adapter:
            with pytest.raises(EmbeddingError) as exc_info:
                await adapter.generate_embedding("Test text")
            
            assert "Failed to generate embeddings after 4 attempts" in str(exc_info.value)
            assert attempt_count == 4  # max_retries=3 means 4 total attempts
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, ollama_config):
        """Test handling of timeout errors."""
        # Arrange
        mock_client = httpx.AsyncClient()
        
        async def mock_post(url, **kwargs):
            raise httpx.TimeoutException("Request timeout")
        
        mock_client.post = mock_post
        
        # Act & Assert
        async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
            with pytest.raises(EmbeddingError) as exc_info:
                await adapter.generate_embedding("Test text")
            
            assert "Failed to connect to Ollama" in str(exc_info.value)
            assert exc_info.value.original_error is not None


class TestConfigurationAndInitialization:
    """Test configuration validation and adapter initialization."""
    
    @pytest.mark.asyncio
    async def test_adapter_initialization_with_valid_config(self, ollama_config):
        """Test adapter initialization with valid configuration."""
        # Act
        async with OllamaEmbeddingAdapter(ollama_config) as adapter:
            # Assert
            assert adapter._config.base_url == "http://localhost:11434"
            assert adapter._config.model_name == "nomic-embed-text"
            assert adapter._config.timeout == 30
            assert adapter._config.max_retries == 1
            assert adapter._config.batch_size == 2
            assert adapter.get_embedding_dimension() == 768
    
    @pytest.mark.asyncio
    async def test_adapter_with_custom_client(self, ollama_config):
        """Test adapter initialization with custom HTTP client."""
        # Arrange
        custom_client = httpx.AsyncClient(timeout=60)
        
        # Act
        async with OllamaEmbeddingAdapter(ollama_config, custom_client) as adapter:
            # Assert
            assert adapter._client is custom_client
    
    def test_config_validation_missing_base_url(self, monkeypatch):
        """Test configuration validation with missing base URL."""
        # Arrange - Clear any existing OLLAMA_BASE_URL
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        
        # Act & Assert
        with pytest.raises(ConfigValidationError) as exc_info:
            OllamaConfig.from_env()
        
        assert "OLLAMA_BASE_URL environment variable is required" in str(exc_info.value)
    
    def test_config_validation_invalid_url_format(self, monkeypatch):
        """Test configuration validation with invalid URL format."""
        # Arrange
        monkeypatch.setenv("OLLAMA_BASE_URL", "invalid-url")
        
        # Act & Assert
        with pytest.raises(ConfigValidationError) as exc_info:
            OllamaConfig.from_env()
        
        assert "must be a valid HTTP/HTTPS URL" in str(exc_info.value)
    
    def test_config_validation_invalid_numeric_values(self, monkeypatch):
        """Test configuration validation with invalid numeric values."""
        # Arrange
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_TIMEOUT", "invalid")
        
        # Act & Assert
        with pytest.raises(ConfigValidationError) as exc_info:
            OllamaConfig.from_env()
        
        assert "Invalid numeric configuration value" in str(exc_info.value)