"""Processing configuration settings."""

import os
from dataclasses import dataclass
from typing import Optional
from .config_validation import ConfigValidationError


@dataclass
class ProcessingConfig:
    """Configuration for document processing."""
    
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 100
    supported_extensions: tuple = (".txt",)
    
    @classmethod
    def from_env(cls) -> "ProcessingConfig":
        """Load processing configuration from environment variables.
        
        Optional environment variables:
        - PROCESSING_CHUNK_SIZE: Size of text chunks in characters (default: 1000)
        - PROCESSING_CHUNK_OVERLAP: Overlap between chunks in characters (default: 200)
        - PROCESSING_MAX_FILE_SIZE_MB: Maximum file size in MB (default: 100)
        - PROCESSING_SUPPORTED_EXTENSIONS: Comma-separated file extensions (default: .txt)
        
        Returns:
            ProcessingConfig: Configured instance
            
        Raises:
            ConfigValidationError: If configuration values are invalid
        """
        try:
            chunk_size = int(os.getenv("PROCESSING_CHUNK_SIZE", "1000"))
            chunk_overlap = int(os.getenv("PROCESSING_CHUNK_OVERLAP", "200"))
            max_file_size_mb = int(os.getenv("PROCESSING_MAX_FILE_SIZE_MB", "100"))
        except ValueError as e:
            raise ConfigValidationError(f"Invalid numeric configuration value: {e}")
        
        # Parse supported extensions
        extensions_str = os.getenv("PROCESSING_SUPPORTED_EXTENSIONS", ".txt")
        supported_extensions = tuple(
            ext.strip() for ext in extensions_str.split(",") if ext.strip()
        )
        
        # Validate values
        if chunk_size <= 0:
            raise ConfigValidationError("PROCESSING_CHUNK_SIZE must be a positive integer")
        
        if chunk_overlap < 0:
            raise ConfigValidationError("PROCESSING_CHUNK_OVERLAP must be non-negative")
        
        if chunk_overlap >= chunk_size:
            raise ConfigValidationError("PROCESSING_CHUNK_OVERLAP must be less than chunk size")
        
        if max_file_size_mb <= 0:
            raise ConfigValidationError("PROCESSING_MAX_FILE_SIZE_MB must be a positive integer")
        
        if not supported_extensions:
            raise ConfigValidationError("At least one file extension must be supported")
        
        # Ensure extensions start with dot
        normalized_extensions = []
        for ext in supported_extensions:
            if not ext.startswith("."):
                ext = "." + ext
            normalized_extensions.append(ext.lower())
        
        return cls(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            max_file_size_mb=max_file_size_mb,
            supported_extensions=tuple(normalized_extensions)
        )
    
    def validate(self) -> None:
        """Validate the configuration settings.
        
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if self.chunk_size <= 0:
            raise ConfigValidationError("Chunk size must be positive")
        
        if self.chunk_overlap < 0:
            raise ConfigValidationError("Chunk overlap must be non-negative")
        
        if self.chunk_overlap >= self.chunk_size:
            raise ConfigValidationError("Chunk overlap must be less than chunk size")
        
        if self.max_file_size_mb <= 0:
            raise ConfigValidationError("Max file size must be positive")
        
        if not self.supported_extensions:
            raise ConfigValidationError("At least one file extension must be supported")
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024