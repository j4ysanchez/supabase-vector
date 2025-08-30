"""Tests for the simplified embedding client."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import httpx

from vector_db.embedding import EmbeddingClient


class TestEmbeddingClient:
    """Test the simplified embedding client."""
    
    @pytest.fixture
    def embedding_client(self):
        """Create an embedding client for testing."""
        return EmbeddingClient()
    
    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx client."""
        mock_client = AsyncMock()
        mock_response = Mock()  # Use regular Mock for response
        mock_response.raise_for_status = Mock()  # Synchronous method
        mock_response.json = Mock(return_value={"embedding": [0.1] * 768})  # Synchronous method
        mock_response.status_code = 200
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.get = AsyncMock(return_value=mock_response)
        
        # Add context manager methods
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        return mock_client
    
    def test_embedding_client_initialization(self, embedding_client):
        """Test embedding client initialization."""
        assert embedding_client.base_url is not None
        assert embedding_client.model is not None
        assert embedding_client.timeout > 0
        assert embedding_client.max_retries >= 0
        assert embedding_client.batch_size > 0
    
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, embedding_client, mock_httpx_client):
        """Test successful embedding generation."""
        # Mock the context manager properly
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            embedding = await embedding_client.generate_embedding("test text")
            
            assert isinstance(embedding, list)
            assert len(embedding) == 768
            assert all(isinstance(x, float) for x in embedding)
            
            # Verify the API call
            mock_httpx_client.post.assert_called_once()
            call_args = mock_httpx_client.post.call_args
            assert "/api/embeddings" in call_args[0][0]
            assert call_args[1]["json"]["prompt"] == "test text"
    
    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, embedding_client):
        """Test embedding generation with empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await embedding_client.generate_embedding("")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await embedding_client.generate_embedding("   ")
    
    @pytest.mark.asyncio
    async def test_generate_embedding_http_error(self, embedding_client):
        """Test embedding generation with HTTP error."""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Server error", request=Mock(), response=Mock()
        ))
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(Exception, match="Embedding generation failed"):
                await embedding_client.generate_embedding("test text")
    
    @pytest.mark.asyncio
    async def test_generate_embedding_invalid_response(self, embedding_client):
        """Test embedding generation with invalid response format."""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(return_value={"invalid": "response"})  # Missing 'embedding' key
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(Exception, match="Embedding generation failed"):
                await embedding_client.generate_embedding("test text")
    
    @pytest.mark.asyncio
    async def test_generate_embedding_retry_logic(self, embedding_client):
        """Test retry logic on failures."""
        mock_client = AsyncMock()
        
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status = Mock(side_effect=httpx.ConnectError("Connection failed"))
        
        mock_response_success = Mock()
        mock_response_success.raise_for_status = Mock()
        mock_response_success.json = Mock(return_value={"embedding": [0.1] * 768})
        
        mock_client.post = AsyncMock(side_effect=[mock_response_fail, mock_response_success])
        
        # Add context manager methods
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with patch('asyncio.sleep'):  # Speed up the test
                embedding = await embedding_client.generate_embedding("test text")
                
                assert len(embedding) == 768
                assert mock_client.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, embedding_client, mock_httpx_client):
        """Test batch embedding generation."""
        texts = ["text 1", "text 2", "text 3"]
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            embeddings = await embedding_client.generate_embeddings(texts)
            
            assert len(embeddings) == 3
            assert all(len(emb) == 768 for emb in embeddings)
            assert mock_httpx_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_empty_list(self, embedding_client):
        """Test batch embedding generation with empty list."""
        embeddings = await embedding_client.generate_embeddings([])
        assert embeddings == []
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_large_batch(self, embedding_client, mock_httpx_client):
        """Test batch processing with batch size limits."""
        # Create more texts than batch size
        texts = [f"text {i}" for i in range(10)]
        embedding_client.batch_size = 3  # Small batch size for testing
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            embeddings = await embedding_client.generate_embeddings(texts)
            
            assert len(embeddings) == 10
            # Should make 10 calls (one per text)
            assert mock_httpx_client.post.call_count == 10
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, embedding_client):
        """Test successful health check."""
        mock_client = AsyncMock()
        mock_response = Mock(status_code=200)  # Use regular Mock for response
        mock_client.get = AsyncMock(return_value=mock_response)
        
        # Add context manager methods
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            is_healthy = await embedding_client.health_check()
            
            assert is_healthy is True
            mock_client.get.assert_called_once_with(f"{embedding_client.base_url}/api/tags")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, embedding_client):
        """Test health check failure."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            is_healthy = await embedding_client.health_check()
            
            assert is_healthy is False