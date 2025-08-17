"""Main application configuration."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from .supabase_config import SupabaseConfig
from .ollama_config import OllamaConfig
from .processing_config import ProcessingConfig
from .logging_config import LoggingConfig
from .config_validation import ConfigValidationError


@dataclass
class ApplicationConfig:
    """Main application configuration containing all subsystem configurations."""
    
    supabase: SupabaseConfig
    ollama: OllamaConfig
    processing: ProcessingConfig
    logging: LoggingConfig
    
    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "ApplicationConfig":
        """Load application configuration from environment variables.
        
        Args:
            env_file: Optional path to .env file to load
            
        Returns:
            ApplicationConfig: Fully configured application instance
            
        Raises:
            ConfigValidationError: If any configuration is invalid
        """
        # Load .env file if specified or if default exists
        if env_file:
            if not env_file.exists():
                raise ConfigValidationError(f"Environment file not found: {env_file}")
            load_dotenv(env_file)
        else:
            # Try to load default .env file from current directory
            default_env = Path(".env")
            if default_env.exists():
                load_dotenv(default_env)
        
        try:
            # Load all subsystem configurations
            supabase = SupabaseConfig.from_env()
            ollama = OllamaConfig.from_env()
            processing = ProcessingConfig.from_env()
            logging = LoggingConfig.from_env()
            
            config = cls(
                supabase=supabase,
                ollama=ollama,
                processing=processing,
                logging=logging
            )
            
            # Validate the complete configuration
            config.validate()
            
            return config
            
        except ConfigValidationError:
            # Re-raise configuration errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions in ConfigValidationError
            raise ConfigValidationError(f"Failed to load configuration: {e}")
    
    def validate(self) -> None:
        """Validate all configuration settings.
        
        Raises:
            ConfigValidationError: If any configuration is invalid
        """
        try:
            self.supabase.validate()
        except ConfigValidationError as e:
            raise ConfigValidationError(f"Supabase configuration error: {e}")
        
        try:
            self.ollama.validate()
        except ConfigValidationError as e:
            raise ConfigValidationError(f"Ollama configuration error: {e}")
        
        try:
            self.processing.validate()
        except ConfigValidationError as e:
            raise ConfigValidationError(f"Processing configuration error: {e}")
        
        try:
            self.logging.validate()
        except ConfigValidationError as e:
            raise ConfigValidationError(f"Logging configuration error: {e}")
    
    def setup_logging(self) -> None:
        """Configure logging using the logging configuration."""
        self.logging.configure_logging()
    
    def get_required_env_vars(self) -> list[str]:
        """Get list of required environment variables."""
        return [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_KEY or SUPABASE_KEY", 
            "OLLAMA_BASE_URL"
        ]
    
    def get_optional_env_vars(self) -> list[str]:
        """Get list of optional environment variables with their defaults."""
        return [
            "SUPABASE_TABLE_NAME (default: documents)",
            "SUPABASE_TIMEOUT (default: 30)",
            "SUPABASE_MAX_RETRIES (default: 3)",
            "OLLAMA_MODEL_NAME (default: nomic-embed-text)",
            "OLLAMA_TIMEOUT (default: 60)",
            "OLLAMA_MAX_RETRIES (default: 3)",
            "OLLAMA_BATCH_SIZE (default: 32)",
            "PROCESSING_CHUNK_SIZE (default: 1000)",
            "PROCESSING_CHUNK_OVERLAP (default: 200)",
            "PROCESSING_MAX_FILE_SIZE_MB (default: 100)",
            "PROCESSING_SUPPORTED_EXTENSIONS (default: .txt)",
            "LOG_LEVEL (default: INFO)",
            "LOG_FORMAT (default: standard format)",
            "LOG_DATE_FORMAT (default: %Y-%m-%d %H:%M:%S)",
            "LOG_FILE (default: None, console only)"
        ]
    
    def print_config_help(self) -> str:
        """Generate help text for configuration setup."""
        help_text = """
Configuration Setup Help
========================

Required Environment Variables:
"""
        for var in self.get_required_env_vars():
            help_text += f"  - {var}\n"
        
        help_text += "\nOptional Environment Variables:\n"
        for var in self.get_optional_env_vars():
            help_text += f"  - {var}\n"
        
        help_text += """
Example .env file:
------------------
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key-here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=nomic-embed-text
LOG_LEVEL=INFO
"""
        return help_text