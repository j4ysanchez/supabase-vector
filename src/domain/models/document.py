"""Document domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with its content and metadata."""
    
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Represents a document with its chunks and metadata."""
    
    filename: str
    file_path: Path
    content_hash: str
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ProcessingResult:
    """Result of document processing operation."""
    
    document: Document
    success: bool
    chunks_processed: int
    error_message: Optional[str] = None