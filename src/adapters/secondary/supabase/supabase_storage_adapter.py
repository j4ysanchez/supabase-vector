"""Supabase storage adapter implementation."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.domain.exceptions import StorageError
from src.domain.models.document import Document, DocumentChunk
from src.infrastructure.config.supabase_config import SupabaseConfig
from src.ports.secondary.storage_port import StoragePort
from .retry_utils import with_retry

logger = logging.getLogger(__name__)


class SupabaseStorageAdapter(StoragePort):
    """Supabase implementation of the StoragePort interface."""
    
    def __init__(self, config: SupabaseConfig):
        """Initialize the Supabase storage adapter.
        
        Args:
            config: Supabase configuration settings
        """
        self._config = config
        self._client = None
        
    async def _get_client(self):
        """Get or create the Supabase client."""
        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self._config.url, self._config.service_key)
                logger.info(f"Initialized Supabase client for URL: {self._config.url}")
            except ImportError:
                raise StorageError(
                    "Supabase client not available. Install with: pip install supabase"
                )
        return self._client
    
    @with_retry(max_attempts=3, base_delay=1.0, max_delay=60.0)
    async def store_document(self, document: Document) -> bool:
        """Store a document with its chunks and embeddings.
        
        Args:
            document: The document to store with all its chunks
            
        Returns:
            bool: True if storage was successful, False otherwise
            
        Raises:
            StorageError: If storage operation fails
        """
        try:
            client = await self._get_client()
            
            # Generate document ID if not present
            if document.id is None:
                document.id = uuid4()
            
            # Prepare document records for each chunk
            records = []
            for chunk in document.chunks:
                record = {
                    'id': uuid4(),
                    'document_id': str(document.id),
                    'filename': document.filename,
                    'file_path': str(document.file_path),
                    'content_hash': document.content_hash,
                    'chunk_index': chunk.chunk_index,
                    'content': chunk.content,
                    'embedding': chunk.embedding,
                    'metadata': {
                        'document_metadata': document.metadata,
                        'chunk_metadata': chunk.metadata
                    },
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                records.append(record)
            
            # Store all chunks in a single batch operation
            result = await client.insert_records(self._config.table_name, records)
            
            if result.get('success', False):
                logger.info(f"Successfully stored document {document.filename} with {len(records)} chunks")
                return True
            else:
                logger.error(f"Failed to store document {document.filename}: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing document {document.filename}: {e}")
            raise StorageError(f"Failed to store document: {e}", original_error=e)
    
    @with_retry(max_attempts=3, base_delay=1.0, max_delay=60.0)
    async def retrieve_document(self, document_id: UUID) -> Optional[Document]:
        """Retrieve a document by its ID.
        
        Args:
            document_id: The unique identifier of the document
            
        Returns:
            Optional[Document]: The document if found, None otherwise
            
        Raises:
            StorageError: If retrieval operation fails
        """
        try:
            client = await self._get_client()
            
            # Query for all chunks of the document
            result = await client.select_records(
                self._config.table_name,
                filters={'document_id': str(document_id)},
                order_by='chunk_index'
            )
            
            if not result.get('success', False) or not result.get('data'):
                return None
            
            records = result['data']
            if not records:
                return None
            
            # Reconstruct document from chunks
            first_record = records[0]
            chunks = []
            
            for record in records:
                stored_metadata = record.get('metadata', {})
                chunk_metadata = stored_metadata.get('chunk_metadata', {})
                
                chunk = DocumentChunk(
                    content=record['content'],
                    chunk_index=record['chunk_index'],
                    embedding=record.get('embedding'),
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
            
            # Extract document metadata from the first record
            first_stored_metadata = first_record.get('metadata', {})
            document_metadata = first_stored_metadata.get('document_metadata', {})
            
            document = Document(
                id=UUID(first_record['document_id']),
                filename=first_record['filename'],
                file_path=Path(first_record['file_path']),
                content_hash=first_record['content_hash'],
                chunks=chunks,
                metadata=document_metadata,
                created_at=datetime.fromisoformat(first_record['created_at']) if first_record.get('created_at') else None,
                updated_at=datetime.fromisoformat(first_record['updated_at']) if first_record.get('updated_at') else None
            )
            
            logger.info(f"Successfully retrieved document {document.filename} with {len(chunks)} chunks")
            return document
            
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            raise StorageError(f"Failed to retrieve document: {e}", original_error=e)
    
    @with_retry(max_attempts=3, base_delay=1.0, max_delay=60.0)
    async def find_by_hash(self, content_hash: str) -> Optional[Document]:
        """Find a document by its content hash.
        
        Args:
            content_hash: The SHA-256 hash of the document content
            
        Returns:
            Optional[Document]: The document if found, None otherwise
            
        Raises:
            StorageError: If search operation fails
        """
        try:
            client = await self._get_client()
            
            # Query for document by content hash
            result = await client.select_records(
                self._config.table_name,
                filters={'content_hash': content_hash},
                order_by='chunk_index',
                limit=1
            )
            
            if not result.get('success', False) or not result.get('data'):
                return None
            
            records = result['data']
            if not records:
                return None
            
            # Get the document_id from the first record and retrieve full document
            document_id = UUID(records[0]['document_id'])
            return await self.retrieve_document(document_id)
            
        except Exception as e:
            logger.error(f"Error finding document by hash {content_hash}: {e}")
            raise StorageError(f"Failed to find document by hash: {e}", original_error=e)
    
    @with_retry(max_attempts=3, base_delay=1.0, max_delay=60.0)
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
        try:
            client = await self._get_client()
            
            # Get distinct document IDs with pagination
            result = await client.select_distinct_documents(
                self._config.table_name,
                limit=limit,
                offset=offset
            )
            
            if not result.get('success', False):
                raise StorageError(f"Failed to list documents: {result.get('error', 'Unknown error')}")
            
            document_ids = result.get('data', [])
            documents = []
            
            # Retrieve each document
            for doc_id in document_ids:
                document = await self.retrieve_document(UUID(doc_id))
                if document:
                    documents.append(document)
            
            logger.info(f"Successfully listed {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise StorageError(f"Failed to list documents: {e}", original_error=e)
    
    @with_retry(max_attempts=3, base_delay=1.0, max_delay=60.0)
    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document and all its chunks.
        
        Args:
            document_id: The unique identifier of the document to delete
            
        Returns:
            bool: True if deletion was successful, False if document not found
            
        Raises:
            StorageError: If deletion operation fails
        """
        try:
            client = await self._get_client()
            
            # Delete all chunks for the document
            result = await client.delete_records(
                self._config.table_name,
                filters={'document_id': str(document_id)}
            )
            
            if result.get('success', False):
                deleted_count = result.get('count', 0)
                if deleted_count > 0:
                    logger.info(f"Successfully deleted document {document_id} ({deleted_count} chunks)")
                    return True
                else:
                    logger.info(f"Document {document_id} not found for deletion")
                    return False
            else:
                logger.error(f"Failed to delete document {document_id}: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise StorageError(f"Failed to delete document: {e}", original_error=e)
    
    async def health_check(self) -> bool:
        """Check if the storage system is healthy and accessible.
        
        Returns:
            bool: True if storage is healthy, False otherwise
        """
        try:
            client = await self._get_client()
            
            # Perform a simple query to check connectivity
            result = await client.health_check(self._config.table_name)
            
            if result.get('success', False):
                logger.info("Supabase storage health check passed")
                return True
            else:
                logger.warning(f"Supabase storage health check failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Supabase storage health check error: {e}")
            return False

