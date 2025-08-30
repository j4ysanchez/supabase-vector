"""Embedding port interface for text embedding generation."""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingPort(ABC):
    """Abstract interface for text embedding generation operations."""
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text strings.
        
        Args:
            texts: List of text strings to generate embeddings for
            
        Returns:
            List[List[float]]: List of embedding vectors, one for each input text
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string.
        
        Args:
            text: Text string to generate embedding for
            
        Returns:
            List[float]: Embedding vector for the input text
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the embedding service is healthy and accessible.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this service.
        
        Returns:
            int: The dimension of embedding vectors
        """
        pass