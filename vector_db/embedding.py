"""Direct Ollama embedding client - no interfaces, no complexity."""

import asyncio
import logging
from typing import List
import httpx

from .config import get_config

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Simple Ollama embedding client."""
    
    def __init__(self):
        """Initialize with configuration."""
        config = get_config()
        self.base_url = config.ollama_url
        self.model = config.ollama_model
        self.timeout = config.ollama_timeout
        self.max_retries = config.ollama_max_retries
        self.batch_size = config.ollama_batch_size
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List[float]: Embedding vector
            
        Raises:
            Exception: If embedding generation fails after retries
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model, "prompt": text}
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    if "embedding" not in data:
                        raise ValueError("Invalid response format from Ollama")
                    
                    embedding = data["embedding"]
                    if not isinstance(embedding, list) or not embedding:
                        raise ValueError("Invalid embedding format")
                    
                    logger.debug(f"Generated embedding with dimension {len(embedding)}")
                    return embedding
                    
            except Exception as e:
                if attempt == self.max_retries:
                    logger.error(f"Failed to generate embedding after {self.max_retries + 1} attempts: {e}")
                    raise Exception(f"Embedding generation failed: {e}")
                
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Embedding attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Process in batches to avoid overwhelming the service
        results = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            logger.debug(f"Processing batch {i//self.batch_size + 1} with {len(batch)} texts")
            
            # Generate embeddings concurrently within batch
            batch_tasks = [self.generate_embedding(text) for text in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
        logger.info(f"Successfully generated {len(results)} embeddings")
        return results
    
    async def health_check(self) -> bool:
        """Check if Ollama service is available.
        
        Returns:
            bool: True if service is healthy
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False