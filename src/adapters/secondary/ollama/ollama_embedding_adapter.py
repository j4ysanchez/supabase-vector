"""Ollama embedding adapter implementation."""

import asyncio
import logging
from typing import List, Dict, Any
import httpx

from src.ports.secondary.embedding_port import EmbeddingPort
from src.config import get_ollama_config
from src.domain.exceptions import EmbeddingError


logger = logging.getLogger(__name__)


class OllamaEmbeddingAdapter(EmbeddingPort):
    """Ollama implementation of the EmbeddingPort interface."""
    
    def __init__(self, config=None, client: httpx.AsyncClient = None):
        """Initialize the Ollama embedding adapter.
        
        Args:
            config: Optional Ollama configuration settings (uses global config if None)
            client: Optional httpx client for testing purposes
        """
        self._config = config or get_ollama_config()
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(self._config.timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        self._embedding_dimension = 768  # nomic-embed-text produces 768-dimensional embeddings
        
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text strings.
        
        Args:
            texts: List of text strings to generate embeddings for
            
        Returns:
            List[List[float]]: List of embedding vectors, one for each input text
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Process texts in batches to avoid overwhelming the service
        embeddings = []
        batch_size = self._config.batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._generate_batch_embeddings(batch)
            embeddings.extend(batch_embeddings)
        
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string.
        
        Args:
            text: Text string to generate embedding for
            
        Returns:
            List[float]: Embedding vector for the input text
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]
    
    async def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts with retry logic.
        
        Args:
            texts: List of text strings to generate embeddings for
            
        Returns:
            List[List[float]]: List of embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails after all retries
        """
        last_error = None
        
        for attempt in range(self._config.max_retries + 1):
            try:
                return await self._make_embedding_request(texts)
            except Exception as e:
                last_error = e
                if attempt < self._config.max_retries:
                    delay = min(2 ** attempt, 30)  # Exponential backoff with max 30s
                    logger.warning(
                        f"Embedding request failed (attempt {attempt + 1}/{self._config.max_retries + 1}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All embedding request attempts failed: {e}")
        
        raise EmbeddingError(
            f"Failed to generate embeddings after {self._config.max_retries + 1} attempts: {last_error}",
            original_error=last_error
        )
    
    async def _make_embedding_request(self, texts: List[str]) -> List[List[float]]:
        """Make the actual HTTP request to Ollama for embeddings.
        
        Args:
            texts: List of text strings to generate embeddings for
            
        Returns:
            List[List[float]]: List of embedding vectors
            
        Raises:
            EmbeddingError: If the request fails
        """
        url = f"{self._config.base_url}/api/embeddings"
        
        # Prepare requests for each text
        embeddings = []
        
        for text in texts:
            payload = {
                "model": self._config.model_name,
                "prompt": text
            }
            
            try:
                response = await self._client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                if "embedding" not in result:
                    raise EmbeddingError(f"Invalid response format: missing 'embedding' field")
                
                embedding = result["embedding"]
                
                if not isinstance(embedding, list) or not embedding:
                    raise EmbeddingError(f"Invalid embedding format: expected non-empty list")
                
                # Validate embedding dimension
                if len(embedding) != self._embedding_dimension:
                    logger.warning(
                        f"Unexpected embedding dimension: got {len(embedding)}, expected {self._embedding_dimension}"
                    )
                    self._embedding_dimension = len(embedding)
                
                embeddings.append(embedding)
                
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
                logger.error(f"Ollama API error: {error_msg}")
                raise EmbeddingError(f"Ollama API request failed: {error_msg}", original_error=e)
            
            except httpx.RequestError as e:
                error_msg = f"Network error: {str(e)}"
                logger.error(f"Ollama connection error: {error_msg}")
                raise EmbeddingError(f"Failed to connect to Ollama: {error_msg}", original_error=e)
            
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Ollama embedding error: {error_msg}")
                raise EmbeddingError(f"Embedding generation failed: {error_msg}", original_error=e)
        
        return embeddings
    
    async def health_check(self) -> bool:
        """Check if the Ollama service is healthy and accessible.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            # Try to get the list of available models
            url = f"{self._config.base_url}/api/tags"
            response = await self._client.get(url)
            response.raise_for_status()
            
            result = response.json()
            
            # Check if our model is available
            if "models" in result:
                available_models = [model.get("name", "") for model in result["models"]]
                if self._config.model_name not in available_models:
                    logger.warning(
                        f"Model '{self._config.model_name}' not found in available models: {available_models}"
                    )
                    return False
            
            logger.info("Ollama service health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this service.
        
        Returns:
            int: The dimension of embedding vectors
        """
        return self._embedding_dimension
    
    async def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        if self._client:
            await self._client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()