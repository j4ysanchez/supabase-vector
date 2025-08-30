"""Main application logic - simple and direct."""

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from .config import config, get_config
from .models import Document
from .embedding import EmbeddingClient
from .storage import StorageClient

logger = logging.getLogger(__name__)


class VectorDB:
    """Simple vector database implementation.
    
    No interfaces, no dependency injection, no over-engineering.
    Just a simple class that does what it needs to do.
    """
    
    def __init__(self):
        """Initialize the vector database."""
        self.config = config
        self.embedding_client = EmbeddingClient()
        self.storage_client = StorageClient()
        
        # Setup logging
        self.config.setup_logging()
        logger.info("VectorDB initialized")
    
    async def ingest_file(self, file_path: Path) -> str:
        """Ingest a file into the vector database.
        
        Args:
            file_path: Path to the file to ingest
            
        Returns:
            str: Success message with document ID
            
        Raises:
            Exception: If ingestion fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.config.max_file_size_bytes:
            raise ValueError(f"File too large: {file_size} bytes (max: {self.config.max_file_size_bytes})")
        
        # Check file extension
        if file_path.suffix.lower() not in self.config.extensions_list:
            raise ValueError(f"Unsupported file type: {file_path.suffix} (supported: {self.config.extensions_list})")
        
        logger.info(f"Ingesting file: {file_path}")
        
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8')
            
            # Generate content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Check if document already exists
            existing_docs = self.storage_client.list_documents()
            for doc in existing_docs:
                if doc.metadata.get('content_hash') == content_hash:
                    logger.info(f"Document already exists with hash: {content_hash}")
                    return f"Document {file_path.name} already exists (ID: {doc.id})"
            
            # Generate embedding
            logger.info("Generating embedding...")
            embedding = await self.embedding_client.generate_embedding(content)
            
            # Create document
            doc = Document(
                filename=file_path.name,
                content=content,
                embedding=embedding,
                metadata={
                    'content_hash': content_hash,
                    'file_size': file_size,
                    'file_path': str(file_path),
                    'embedding_dimension': len(embedding)
                }
            )
            
            # Store document
            doc_id = self.storage_client.store_document(doc)
            
            success_msg = f"Successfully ingested {file_path.name} (ID: {doc_id})"
            logger.info(success_msg)
            return success_msg
            
        except Exception as e:
            error_msg = f"Failed to ingest {file_path.name}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def ingest_directory(self, dir_path: Path, recursive: bool = False) -> List[str]:
        """Ingest all supported files in a directory.
        
        Args:
            dir_path: Path to directory
            recursive: Whether to search recursively
            
        Returns:
            List[str]: List of success/error messages
        """
        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Directory not found: {dir_path}")
        
        logger.info(f"Ingesting directory: {dir_path} (recursive: {recursive})")
        
        # Find supported files
        pattern = "**/*" if recursive else "*"
        files = []
        
        for ext in self.config.extensions_list:
            files.extend(dir_path.glob(f"{pattern}{ext}"))
        
        if not files:
            return [f"No supported files found in {dir_path}"]
        
        logger.info(f"Found {len(files)} files to ingest")
        
        # Ingest files
        results = []
        for file_path in files:
            try:
                result = await self.ingest_file(file_path)
                results.append(result)
            except Exception as e:
                error_msg = f"Failed to ingest {file_path.name}: {e}"
                results.append(error_msg)
                logger.error(error_msg)
        
        return results
    
    def search_by_text(self, query: str, limit: int = 10) -> List[Document]:
        """Search documents by text content.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List[Document]: Matching documents
        """
        logger.info(f"Searching for: '{query}' (limit: {limit})")
        return self.storage_client.search_by_content(query, limit)
    
    def get_document(self, doc_id: UUID) -> Optional[Document]:
        """Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Optional[Document]: The document if found
        """
        return self.storage_client.get_document(doc_id)
    
    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """List all documents.
        
        Args:
            limit: Maximum results
            offset: Number to skip
            
        Returns:
            List[Document]: List of documents
        """
        return self.storage_client.list_documents(limit, offset)
    
    def delete_document(self, doc_id: UUID) -> bool:
        """Delete a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            bool: True if deleted
        """
        logger.info(f"Deleting document: {doc_id}")
        return self.storage_client.delete_document(doc_id)
    
    async def health_check(self) -> dict:
        """Check health of all services.
        
        Returns:
            dict: Health status of each service
        """
        logger.info("Performing health check...")
        
        # Check Ollama
        ollama_healthy = await self.embedding_client.health_check()
        
        # Check Supabase
        supabase_healthy = self.storage_client.health_check()
        
        status = {
            'ollama': ollama_healthy,
            'supabase': supabase_healthy,
            'overall': ollama_healthy and supabase_healthy
        }
        
        logger.info(f"Health check results: {status}")
        return status
    
    def get_stats(self) -> dict:
        """Get database statistics.
        
        Returns:
            dict: Database statistics
        """
        try:
            docs = self.list_documents(limit=1000)  # Get a reasonable sample
            
            total_docs = len(docs)
            total_size = sum(len(doc.content) for doc in docs)
            avg_size = total_size / total_docs if total_docs > 0 else 0
            
            # File type distribution
            file_types = {}
            for doc in docs:
                ext = Path(doc.filename).suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            
            stats = {
                'total_documents': total_docs,
                'total_content_size': total_size,
                'average_document_size': int(avg_size),
                'file_types': file_types,
                'config': {
                    'chunk_size': self.config.chunk_size,
                    'supported_extensions': self.config.extensions_list,
                    'max_file_size_mb': self.config.max_file_size_mb
                }
            }
            
            logger.info(f"Database stats: {total_docs} documents, {total_size} bytes")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}