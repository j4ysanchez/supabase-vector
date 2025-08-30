"""Unified Pydantic-based configuration for the simplified vector database."""

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings
from typing import Optional


class Config(BaseSettings):
    """Unified configuration class using Pydantic for validation and environment loading."""
    
    # Supabase Configuration
    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_key: str = Field(alias="SUPABASE_KEY")
    supabase_table: str = Field(default="documents", alias="SUPABASE_TABLE_NAME")
    
    # Ollama Configuration  
    ollama_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="nomic-embed-text", alias="OLLAMA_MODEL_NAME")
    
    # Processing Configuration
    chunk_size: int = Field(default=1000, alias="PROCESSING_CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="PROCESSING_CHUNK_OVERLAP")
    max_file_size: int = Field(default=10_000_000, alias="PROCESSING_MAX_FILE_SIZE_MB")  # Will be converted from MB
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    
    model_config = {
        "extra": "ignore",  # Ignore extra environment variables
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,  # Allow both field names and aliases
        "validate_default": True  # Validate default values
    }
    
    @field_validator('supabase_url')
    @classmethod
    def validate_supabase_url(cls, v):
        """Validate that Supabase URL starts with https://."""
        if not v.startswith('https://'):
            raise ValueError('Supabase URL must start with https://')
        return v
    
    @field_validator('chunk_size')
    @classmethod
    def validate_chunk_size(cls, v):
        """Validate chunk size is positive."""
        if v <= 0:
            raise ValueError('Chunk size must be positive')
        return v
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        """Validate chunk overlap is less than chunk size."""
        if info.data and 'chunk_size' in info.data and v >= info.data['chunk_size']:
            raise ValueError('Chunk overlap must be less than chunk size')
        return v
    
    @field_validator('max_file_size')
    @classmethod
    def validate_max_file_size(cls, v):
        """Validate max file size is positive and convert from MB to bytes if needed."""
        if v <= 0:
            raise ValueError('Max file size must be positive')
        # If the value is small (likely in MB), convert to bytes
        if v < 1000:  # Assume values under 1000 are in MB
            return v * 1_000_000
        return v
    
    @field_validator('max_retries')
    @classmethod
    def validate_max_retries(cls, v):
        """Validate max retries is non-negative."""
        if v < 0:
            raise ValueError('Max retries must be non-negative')
        return v
    
    @field_validator('retry_delay')
    @classmethod
    def validate_retry_delay(cls, v):
        """Validate retry delay is non-negative."""
        if v < 0:
            raise ValueError('Retry delay must be non-negative')
        return v
    
    @field_validator('ollama_model')
    @classmethod
    def validate_ollama_model(cls, v):
        """Clean up ollama model name by removing version tags."""
        if isinstance(v, str) and ':' in v:
            return v.split(':')[0]
        return v
    
    def setup_logging(self):
        """Set up logging configuration (for compatibility with old tests)."""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes (compatibility property)."""
        return self.max_file_size
    
    @property
    def extensions_list(self) -> tuple:
        """Get supported file extensions (compatibility property)."""
        return ('.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.yaml', '.yml')
    
    @property
    def max_file_size_mb(self) -> int:
        """Get max file size in MB (compatibility property)."""
        return self.max_file_size // 1_000_000
    
    @property
    def supabase_anon_key(self) -> str:
        """Get supabase key (compatibility property for tests)."""
        return self.supabase_key
    



# Global config instance - will be loaded from environment
config = Config()


def get_config() -> Config:
    """Get the global config instance (compatibility function)."""
    return config