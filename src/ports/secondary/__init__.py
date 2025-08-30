"""Secondary ports package for outbound interfaces."""

from .storage_port import StoragePort
from .embedding_port import EmbeddingPort

__all__ = ['StoragePort', 'EmbeddingPort']