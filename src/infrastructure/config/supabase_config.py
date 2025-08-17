"""Supabase configuration settings."""

import os
from dataclasses import dataclass
from typing import Optional
from .config_validation import ConfigValidationError


@dataclass
class SupabaseConfig:
    """Configuration for Supabase database connection."""
    
    url: str
    service_key: str
    table_name: str = "documents"
    timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> "SupabaseConfig":
        """Load Supabase configuration from environment variables.
        
        Required environment variables:
        - SUPABASE_URL: The Supabase project URL
        - SUPABASE_SERVICE_KEY or SUPABASE_KEY: The Supabase service role key
        
        Optional environment variables:
        - SUPABASE_TABLE_NAME: Table name for documents (default: documents)
        - SUPABASE_TIMEOUT: Connection timeout in seconds (default: 30)
        - SUPABASE_MAX_RETRIES: Maximum retry attempts (default: 3)
        
        Returns:
            SupabaseConfig: Configured instance
            
        Raises:
            ConfigValidationError: If required environment variables are missing
        """
        url = os.getenv("SUPABASE_URL")
        # Try both SUPABASE_SERVICE_KEY and SUPABASE_KEY for backward compatibility
        service_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not url:
            raise ConfigValidationError("SUPABASE_URL environment variable is required")
        
        if not service_key:
            raise ConfigValidationError("SUPABASE_SERVICE_KEY or SUPABASE_KEY environment variable is required")
        
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            raise ConfigValidationError("SUPABASE_URL must be a valid HTTP/HTTPS URL")
        
        # Optional settings with defaults
        table_name = os.getenv("SUPABASE_TABLE_NAME", "documents")
        
        try:
            timeout = int(os.getenv("SUPABASE_TIMEOUT", "30"))
            max_retries = int(os.getenv("SUPABASE_MAX_RETRIES", "3"))
        except ValueError as e:
            raise ConfigValidationError(f"Invalid numeric configuration value: {e}")
        
        if timeout <= 0:
            raise ConfigValidationError("SUPABASE_TIMEOUT must be a positive integer")
        
        if max_retries < 0:
            raise ConfigValidationError("SUPABASE_MAX_RETRIES must be a non-negative integer")
        
        return cls(
            url=url,
            service_key=service_key,
            table_name=table_name,
            timeout=timeout,
            max_retries=max_retries
        )
    
    def validate(self) -> None:
        """Validate the configuration settings.
        
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if not self.url:
            raise ConfigValidationError("Supabase URL cannot be empty")
        
        if not self.service_key:
            raise ConfigValidationError("Supabase service key cannot be empty")
        
        if not self.table_name:
            raise ConfigValidationError("Table name cannot be empty")
        
        if self.timeout <= 0:
            raise ConfigValidationError("Timeout must be positive")
        
        if self.max_retries < 0:
            raise ConfigValidationError("Max retries must be non-negative")