"""Ollama configuration settings."""

import os
from dataclasses import dataclass
from typing import Optional
from .config_validation import ConfigValidationError


@dataclass
class OllamaConfig:
    """Configuration for Ollama embedding service."""
    
    base_url: str
    model_name: str = "nomic-embed-text"
    timeout: int = 60
    max_retries: int = 3
    batch_size: int = 32
    
    @classmethod
    def from_env(cls) -> "OllamaConfig":
        """Load Ollama configuration from environment variables.
        
        Required environment variables:
        - OLLAMA_BASE_URL: The Ollama service base URL
        
        Optional environment variables:
        - OLLAMA_MODEL_NAME: Model name for embeddings (default: nomic-embed-text)
        - OLLAMA_TIMEOUT: Request timeout in seconds (default: 60)
        - OLLAMA_MAX_RETRIES: Maximum retry attempts (default: 3)
        - OLLAMA_BATCH_SIZE: Batch size for embedding requests (default: 32)
        
        Returns:
            OllamaConfig: Configured instance
            
        Raises:
            ConfigValidationError: If required environment variables are missing
        """
        base_url = os.getenv("OLLAMA_BASE_URL")
        
        if not base_url:
            raise ConfigValidationError("OLLAMA_BASE_URL environment variable is required")
        
        # Validate URL format
        if not base_url.startswith(("http://", "https://")):
            raise ConfigValidationError("OLLAMA_BASE_URL must be a valid HTTP/HTTPS URL")
        
        # Remove trailing slash for consistency
        base_url = base_url.rstrip("/")
        
        # Optional settings with defaults
        model_name = os.getenv("OLLAMA_MODEL_NAME", "nomic-embed-text")
        
        try:
            timeout = int(os.getenv("OLLAMA_TIMEOUT", "60"))
            max_retries = int(os.getenv("OLLAMA_MAX_RETRIES", "3"))
            batch_size = int(os.getenv("OLLAMA_BATCH_SIZE", "32"))
        except ValueError as e:
            raise ConfigValidationError(f"Invalid numeric configuration value: {e}")
        
        if timeout <= 0:
            raise ConfigValidationError("OLLAMA_TIMEOUT must be a positive integer")
        
        if max_retries < 0:
            raise ConfigValidationError("OLLAMA_MAX_RETRIES must be a non-negative integer")
        
        if batch_size <= 0:
            raise ConfigValidationError("OLLAMA_BATCH_SIZE must be a positive integer")
        
        return cls(
            base_url=base_url,
            model_name=model_name,
            timeout=timeout,
            max_retries=max_retries,
            batch_size=batch_size
        )
    
    def validate(self) -> None:
        """Validate the configuration settings.
        
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if not self.base_url:
            raise ConfigValidationError("Ollama base URL cannot be empty")
        
        if not self.model_name:
            raise ConfigValidationError("Model name cannot be empty")
        
        if self.timeout <= 0:
            raise ConfigValidationError("Timeout must be positive")
        
        if self.max_retries < 0:
            raise ConfigValidationError("Max retries must be non-negative")
        
        if self.batch_size <= 0:
            raise ConfigValidationError("Batch size must be positive")