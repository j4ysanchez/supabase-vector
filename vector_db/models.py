"""Simple document models."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID


@dataclass
class Document:
    """Simple document representation."""
    filename: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    
    @property
    def content_preview(self) -> str:
        """Get a preview of the document content."""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."
    
    @property
    def embedding_dimension(self) -> Optional[int]:
        """Get the dimension of the embedding vector."""
        return len(self.embedding) if self.embedding else None