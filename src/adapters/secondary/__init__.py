"""Secondary adapters package for outbound integrations."""

from .ollama import OllamaEmbeddingAdapter
from .supabase import SupabaseStorageAdapter

__all__ = ['OllamaEmbeddingAdapter', 'SupabaseStorageAdapter']