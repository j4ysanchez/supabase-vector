"""Storage port interface for document persistence."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.models.document import Document


class StoragePort(ABC):
    """Abstract interface for document storage operations."""
    
    @abstractmethod
    async def store_document(self, document: Document) -> bool:
        """Store a document with its chunks and embeddings.
        
        Args:
            document: The document to store with all its chunks
            
        Returns:
            bool: True if storage was successful, False otherwise
            
        Raises:
            StorageError: If storage operation fails
        """
        pass
    
    @abstractmethod
    async def retrieve_document(self, document_id: UUID) -> Optional[Document]:
        """Retrieve a document by its ID.
        
        Args:
            document_id: The unique identifier of the document
            
        Returns:
            Optional[Document]: The document if found, None otherwise
            
        Raises:
            StorageError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_hash(self, content_hash: str) -> Optional[Document]:
        """Find a document by its content hash.
        
        Args:
            content_hash: The SHA-256 hash of the document content
            
        Returns:
            Optional[Document]: The document if found, None otherwise
            
        Raises:
            StorageError: If search operation fails
        """
        pass
    
    @abstractmethod
    async def list_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """List stored documents with pagination.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List[Document]: List of documents
            
        Raises:
            StorageError: If listing operation fails
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document and all its chunks.
        
        Args:
            document_id: The unique identifier of the document to delete
            
        Returns:
            bool: True if deletion was successful, False if document not found
            
        Raises:
            StorageError: If deletion operation fails
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the storage system is healthy and accessible.
        
        Returns:
            bool: True if storage is healthy, False otherwise
        """
        pass