"""Simplified Vector Database implementation."""

from .main import VectorDB
from .models import Document
from .config import get_config

__version__ = "0.1.0"
__all__ = ["VectorDB", "Document", "get_config"]