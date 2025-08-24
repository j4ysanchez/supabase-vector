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
                    # Each chunk gets its own UUID as the primary key
                    'filename': document.filename,
                    'file_path': str(document.file_path),
                    'content_hash': document.content_hash,
                    'chunk_index': chunk.chunk_index,
                    'content': chunk.content,
                    'embedding': chunk.embedding,
                    'metadata': {
                        'document_id': str(document.id),  # Store document ID in metadata
                        'document_metadata': document.metadata,
                        'chunk_metadata': chunk.metadata
                    }
                }
                records.append(record)
            
            # Store all chunks in a single batch operation
            result = client.table(self._config.table_name).insert(records).execute()
            
            if result.data:
                logger.info(f"Successfully stored document {document.filename} with {len(records)} chunks")
                return True
            else:
                logger.error(f"Failed to store document {document.filename}: No data returned from insert")
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
            
            # Query for all chunks of the document using metadata filter
            # Since document_id is stored in metadata, we need to use a JSON query
            result = client.table(self._config.table_name)\
                .select("*")\
                .eq('metadata->>document_id', str(document_id))\
                .order('chunk_index')\
                .execute()
            
            if not result.data:
                return None
            
            records = result.data
            if not records:
                return None
            
            # Reconstruct document from chunks
            first_record = records[0]
            chunks = []
            
            for record in records:
                stored_metadata = record.get('metadata', {})
                chunk_metadata = stored_metadata.get('chunk_metadata', {})
                
                # Handle embedding - it might be stored as a string or list
                embedding = record.get('embedding')
                if embedding and isinstance(embedding, str):
                    # Parse string representation back to list
                    try:
                        import json
                        embedding = json.loads(embedding.replace('[', '[').replace(']', ']'))
                    except:
                        # If parsing fails, keep as is
                        pass
                
                chunk = DocumentChunk(
                    content=record['content'],
                    chunk_index=record['chunk_index'],
                    embedding=embedding,
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
            
            # Extract document metadata from the first record
            first_stored_metadata = first_record.get('metadata', {})
            document_metadata = first_stored_metadata.get('document_metadata', {})
            
            document = Document(
                id=document_id,
                filename=first_record['filename'],
                file_path=Path(first_record['file_path']),
                content_hash=first_record['content_hash'],
                chunks=chunks,
                metadata=document_metadata,
                created_at=datetime.fromisoformat(first_record['created_at'].replace('Z', '+00:00')) if first_record.get('created_at') else None,
                updated_at=datetime.fromisoformat(first_record['updated_at'].replace('Z', '+00:00')) if first_record.get('updated_at') else None
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
            result = client.table(self._config.table_name)\
                .select("*")\
                .eq('content_hash', content_hash)\
                .order('chunk_index')\
                .limit(1)\
                .execute()
            
            if not result.data:
                return None
            
            records = result.data
            if not records:
                return None
            
            # Get the document_id from the first record's metadata and retrieve full document
            first_metadata = records[0].get('metadata', {})
            document_id_str = first_metadata.get('document_id')
            if document_id_str:
                document_id = UUID(document_id_str)
                return await self.retrieve_document(document_id)
            return None
            
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
            
            # Get distinct document IDs from metadata with pagination
            result = client.table(self._config.table_name)\
                .select("metadata, filename, created_at")\
                .order('created_at', desc=True)\
                .limit(limit * 5)\
                .execute()  # Get more records to account for multiple chunks per document
            
            if not result.data:
                return []
            
            # Get unique document IDs from metadata
            seen_ids = set()
            document_ids = []
            for record in result.data:
                metadata = record.get('metadata', {})
                doc_id = metadata.get('document_id')
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    document_ids.append(doc_id)
                    if len(document_ids) >= limit:  # Respect the limit
                        break
            documents = []
            
            # Retrieve each unique document
            for doc_id in document_ids[offset:offset + limit]:
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
            
            # Delete all chunks for the document using metadata filter
            result = client.table(self._config.table_name)\
                .delete()\
                .eq('metadata->>document_id', str(document_id))\
                .execute()
            
            if result.data is not None:
                deleted_count = len(result.data) if result.data else 0
                if deleted_count > 0:
                    logger.info(f"Successfully deleted document {document_id} ({deleted_count} chunks)")
                    return True
                else:
                    logger.info(f"Document {document_id} not found for deletion")
                    return False
            else:
                logger.error(f"Failed to delete document {document_id}")
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
            result = client.table(self._config.table_name)\
                .select("count", count="exact")\
                .limit(1)\
                .execute()
            
            logger.info(f"Supabase storage health check passed. Table has {result.count} records")
            return True
                
        except Exception as e:
            logger.error(f"Supabase storage health check error: {e}")
            return False

