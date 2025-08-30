"""Simplified configuration management using Pydantic."""

from pathlib import Path
from typing import Optional, Tuple
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import logging


class Config(BaseSettings):
    """Unified application configuration using Pydantic for validation."""
    
    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase service role key")
    supabase_table: str = Field(default="documents", alias="SUPABASE_TABLE_NAME", description="Table name for document storage")
    supabase_timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    supabase_max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    
    # Ollama Configuration  
    ollama_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL", description="Ollama service base URL")
    ollama_model: str = Field(default="nomic-embed-text", alias="OLLAMA_MODEL_NAME", description="Embedding model name")
    ollama_timeout: int = Field(default=60, ge=1, le=600, description="Request timeout in seconds")
    ollama_max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    ollama_batch_size: int = Field(default=32, ge=1, le=1000, description="Batch size for embeddings")
    
    # Processing Configuration
    chunk_size: int = Field(default=1000, ge=100, le=10000, alias="PROCESSING_CHUNK_SIZE", description="Text chunk size in characters")
    chunk_overlap: int = Field(default=200, ge=0, alias="PROCESSING_CHUNK_OVERLAP", description="Overlap between chunks in characters")
    max_file_size_mb: int = Field(default=100, ge=1, le=1000, alias="PROCESSING_MAX_FILE_SIZE_MB", description="Maximum file size in MB")
    supported_extensions: str = Field(default=".txt", alias="PROCESSING_SUPPORTED_EXTENSIONS", description="Comma-separated file extensions")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Optional log file path")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )
    
    def __init__(self, _env_file=None, **kwargs):
        # Handle SUPABASE_KEY fallback
        if "supabase_key" not in kwargs:
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
            if supabase_key:
                kwargs["supabase_key"] = supabase_key
        
        # Allow disabling env file loading for tests
        if _env_file is not None:
            super().__init__(_env_file=_env_file, **kwargs)
        else:
            super().__init__(**kwargs)
    
    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, v):
        """Validate Supabase URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Supabase URL must start with http:// or https://")
        return v.rstrip("/")
    
    @field_validator("ollama_url")
    @classmethod
    def validate_ollama_url(cls, v):
        """Validate Ollama URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Ollama URL must start with http:// or https://")
        return v.rstrip("/")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v_upper
    
    @field_validator("supported_extensions")
    @classmethod
    def validate_extensions(cls, v):
        """Parse and validate file extensions."""
        if isinstance(v, str):
            extensions = [ext.strip() for ext in v.split(",") if ext.strip()]
            # Ensure extensions start with dot
            normalized = []
            for ext in extensions:
                if not ext.startswith("."):
                    ext = "." + ext
                normalized.append(ext.lower())
            return ",".join(normalized)
        return v
    
    @model_validator(mode='after')
    def validate_chunk_overlap(self):
        """Ensure chunk overlap is less than chunk size."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        return self
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def extensions_list(self) -> Tuple[str, ...]:
        """Get supported extensions as a tuple."""
        return tuple(ext.strip() for ext in self.supported_extensions.split(",") if ext.strip())
    
    def setup_logging(self) -> None:
        """Configure logging with current settings."""
        handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        handlers.append(console_handler)
        
        # File handler if specified
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            handlers=handlers,
            force=True
        )
    
    def print_summary(self) -> None:
        """Print a summary of the current configuration."""
        print("Configuration Summary")
        print("=" * 50)
        
        print(f"\n🔗 Supabase:")
        print(f"  URL: {self.supabase_url}")
        print(f"  Table: {self.supabase_table}")
        print(f"  Timeout: {self.supabase_timeout}s")
        print(f"  Max Retries: {self.supabase_max_retries}")
        
        print(f"\n🤖 Ollama:")
        print(f"  URL: {self.ollama_url}")
        print(f"  Model: {self.ollama_model}")
        print(f"  Timeout: {self.ollama_timeout}s")
        print(f"  Max Retries: {self.ollama_max_retries}")
        print(f"  Batch Size: {self.ollama_batch_size}")
        
        print(f"\n📄 Processing:")
        print(f"  Chunk Size: {self.chunk_size} chars")
        print(f"  Chunk Overlap: {self.chunk_overlap} chars")
        print(f"  Max File Size: {self.max_file_size_mb}MB")
        print(f"  Extensions: {self.supported_extensions}")
        
        print(f"\n📝 Logging:")
        print(f"  Level: {self.log_level}")
        print(f"  File: {self.log_file or 'Console only'}")


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
        _config.setup_logging()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment."""
    global _config
    _config = Config()
    _config.setup_logging()
    return _config


# Convenience functions for backward compatibility
def get_supabase_config():
    """Get Supabase configuration as a simple object."""
    config = get_config()
    
    class SupabaseConfig:
        def __init__(self):
            self.url = config.supabase_url
            self.service_key = config.supabase_key
            self.table_name = config.supabase_table
            self.timeout = config.supabase_timeout
            self.max_retries = config.supabase_max_retries
    
    return SupabaseConfig()


def get_ollama_config():
    """Get Ollama configuration as a simple object."""
    config = get_config()
    
    class OllamaConfig:
        def __init__(self):
            self.base_url = config.ollama_url
            self.model_name = config.ollama_model
            self.timeout = config.ollama_timeout
            self.max_retries = config.ollama_max_retries
            self.batch_size = config.ollama_batch_size
    
    return OllamaConfig()

# Test helper functions
def create_test_supabase_config(
    url: str = "https://test.supabase.co",
    service_key: str = "test-key",
    table_name: str = "test_documents",
    timeout: int = 30,
    max_retries: int = 3
):
    """Create a test Supabase configuration object."""
    class SupabaseConfig:
        def __init__(self):
            self.url = url
            self.service_key = service_key
            self.table_name = table_name
            self.timeout = timeout
            self.max_retries = max_retries
    
    return SupabaseConfig()


def create_test_ollama_config(
    base_url: str = "http://localhost:11434",
    model_name: str = "nomic-embed-text",
    timeout: int = 60,
    max_retries: int = 3,
    batch_size: int = 32
):
    """Create a test Ollama configuration object."""
    class OllamaConfig:
        def __init__(self):
            self.base_url = base_url
            self.model_name = model_name
            self.timeout = timeout
            self.max_retries = max_retries
            self.batch_size = batch_size
    
    return OllamaConfig()