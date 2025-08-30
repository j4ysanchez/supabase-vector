"""Simplified Vector Database implementation."""

from .main import VectorDB
from .models import Document, DocumentChunk, ProcessingResult
from .config import Config, config, get_config

__version__ = "0.1.0"
__all__ = ["VectorDB", "Document", "DocumentChunk", "ProcessingResult", "Config", "config", "get_config"]