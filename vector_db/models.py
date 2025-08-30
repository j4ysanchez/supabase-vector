"""Simple dataclass models for the simplified vector database."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from uuid import UUID
import hashlib


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with its content and embedding."""
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Represents a document - supports both old and new usage patterns."""
    filename: str
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    chunks: List[DocumentChunk] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    # Compatibility fields for old tests
    content: Optional[str] = None
    embedding: Optional[List[float]] = None
    id: Optional[UUID] = None
    
    def __post_init__(self):
        """Handle compatibility between old and new usage patterns."""
        # If content is provided but no file_path, generate defaults
        if self.content is not None and self.file_path is None:
            self.file_path = f"/path/to/{self.filename}"
        
        # If content is provided but no content_hash, generate it
        if self.content is not None and self.content_hash is None:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()
        
        # If content and embedding are provided, create a single chunk
        if self.content is not None and self.embedding is not None and not self.chunks:
            chunk = DocumentChunk(
                content=self.content,
                chunk_index=0,
                embedding=self.embedding,
                metadata={}
            )
            self.chunks = [chunk]
    
    @property
    def content_preview(self) -> str:
        """Get a preview of the document content (compatibility property)."""
        if self.content:
            if len(self.content) <= 100:
                return self.content
            return self.content[:97] + "..."
        elif self.chunks:
            first_chunk = self.chunks[0].content
            if len(first_chunk) <= 100:
                return first_chunk
            return first_chunk[:97] + "..."
        return ""
    
    @property
    def embedding_dimension(self) -> Optional[int]:
        """Get the dimension of the embedding vector (compatibility property)."""
        if self.embedding:
            return len(self.embedding)
        elif self.chunks and self.chunks[0].embedding:
            return len(self.chunks[0].embedding)
        return None


@dataclass
class ProcessingResult:
    """Represents the result of processing a document."""
    filename: str
    success: bool
    chunks_processed: int = 0
    error_message: Optional[str] = None
    processing_time: float = 0.0