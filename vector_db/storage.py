"""Direct Supabase storage client - no interfaces, no complexity."""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from .config import get_config
from .models import Document

logger = logging.getLogger(__name__)


class StorageClient:
    """Simple Supabase storage client."""
    
    def __init__(self):
        """Initialize with configuration."""
        config = get_config()
        self.url = config.supabase_url
        self.key = config.supabase_anon_key  # Use anon key for client operations
        self.table = config.supabase_table
        self.timeout = config.supabase_timeout
        self.max_retries = config.supabase_max_retries
        self._client = None
    
    def _get_client(self):
        """Get or create Supabase client."""
        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self.url, self.key)
                logger.info(f"Connected to Supabase: {self.url}")
            except ImportError:
                raise ImportError("Supabase client not installed. Run: pip install supabase")
            except Exception as e:
                raise Exception(f"Failed to connect to Supabase: {e}")
        return self._client
    
    def store_document(self, doc: Document) -> UUID:
        """Store a document and return its ID.
        
        Args:
            doc: Document to store
            
        Returns:
            UUID: The document ID
            
        Raises:
            Exception: If storage fails
        """
        client = self._get_client()
        doc_id = doc.id or uuid4()
        
        data = {
            "id": str(doc_id),
            "filename": doc.filename,
            "content": doc.content,
            "embedding": doc.embedding,
            "metadata": doc.metadata,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            result = client.table(self.table).insert(data).execute()
            if not result.data:
                raise Exception("No data returned from insert operation")
            
            logger.info(f"Stored document: {doc.filename} with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to store document {doc.filename}: {e}")
            raise Exception(f"Storage failed: {e}")
    
    def get_document(self, doc_id: UUID) -> Optional[Document]:
        """Retrieve a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Optional[Document]: The document if found
        """
        client = self._get_client()
        
        try:
            result = client.table(self.table).select("*").eq("id", str(doc_id)).execute()
            
            if not result.data:
                return None
            
            data = result.data[0]
            return Document(
                filename=data["filename"],
                content=data["content"],
                embedding=data.get("embedding"),
                metadata=data.get("metadata", {}),
                id=UUID(data["id"]),
                created_at=datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')) if data.get("created_at") else None
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve document {doc_id}: {e}")
            raise Exception(f"Retrieval failed: {e}")
    
    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """List documents with pagination.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List[Document]: List of documents
        """
        client = self._get_client()
        
        try:
            result = (client.table(self.table)
                     .select("*")
                     .range(offset, offset + limit - 1)
                     .order("created_at", desc=True)
                     .execute())
            
            documents = []
            for data in result.data:
                doc = Document(
                    filename=data["filename"],
                    content=data["content"],
                    embedding=data.get("embedding"),
                    metadata=data.get("metadata", {}),
                    id=UUID(data["id"]),
                    created_at=datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')) if data.get("created_at") else None
                )
                documents.append(doc)
            
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise Exception(f"Listing failed: {e}")
    
    def delete_document(self, doc_id: UUID) -> bool:
        """Delete a document by ID.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        client = self._get_client()
        
        try:
            result = client.table(self.table).delete().eq("id", str(doc_id)).execute()
            
            if result.data:
                logger.info(f"Deleted document: {doc_id}")
                return True
            else:
                logger.warning(f"Document not found for deletion: {doc_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise Exception(f"Deletion failed: {e}")
    
    def search_by_content(self, query: str, limit: int = 10) -> List[Document]:
        """Simple text search in document content.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List[Document]: Matching documents
        """
        client = self._get_client()
        
        try:
            # Simple text search - in a real implementation you'd use vector similarity
            result = (client.table(self.table)
                     .select("*")
                     .ilike("content", f"%{query}%")
                     .limit(limit)
                     .execute())
            
            documents = []
            for data in result.data:
                doc = Document(
                    filename=data["filename"],
                    content=data["content"],
                    embedding=data.get("embedding"),
                    metadata=data.get("metadata", {}),
                    id=UUID(data["id"]),
                    created_at=datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')) if data.get("created_at") else None
                )
                documents.append(doc)
            
            logger.info(f"Found {len(documents)} documents matching '{query}'")
            return documents
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise Exception(f"Search failed: {e}")
    
    def health_check(self) -> bool:
        """Check if Supabase is accessible.
        
        Returns:
            bool: True if healthy
        """
        try:
            client = self._get_client()
            # Simple query to test connection
            result = client.table(self.table).select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.warning(f"Supabase health check failed: {e}")
            return False