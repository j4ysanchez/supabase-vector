"""Logging configuration settings."""

import os
import logging
from dataclasses import dataclass
from typing import Optional
from .config_validation import ConfigValidationError


@dataclass
class LoggingConfig:
    """Configuration for application logging."""
    
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_file: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Load logging configuration from environment variables.
        
        Optional environment variables:
        - LOG_LEVEL: Logging level (default: INFO)
        - LOG_FORMAT: Log message format (default: standard format)
        - LOG_DATE_FORMAT: Date format for log messages (default: %Y-%m-%d %H:%M:%S)
        - LOG_FILE: Path to log file (default: None, logs to console)
        
        Returns:
            LoggingConfig: Configured instance
            
        Raises:
            ConfigValidationError: If configuration values are invalid
        """
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        date_format = os.getenv("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
        log_file = os.getenv("LOG_FILE")
        
        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level not in valid_levels:
            raise ConfigValidationError(
                f"Invalid log level '{level}'. Must be one of: {', '.join(valid_levels)}"
            )
        
        return cls(
            level=level,
            format=log_format,
            date_format=date_format,
            log_file=log_file
        )
    
    def validate(self) -> None:
        """Validate the configuration settings.
        
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level not in valid_levels:
            raise ConfigValidationError(
                f"Invalid log level '{self.level}'. Must be one of: {', '.join(valid_levels)}"
            )
        
        if not self.format:
            raise ConfigValidationError("Log format cannot be empty")
        
        if not self.date_format:
            raise ConfigValidationError("Date format cannot be empty")
    
    def get_log_level(self) -> int:
        """Get the numeric log level for the logging module."""
        return getattr(logging, self.level)
    
    def configure_logging(self) -> None:
        """Configure the Python logging system with these settings."""
        handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(self.format, self.date_format)
        )
        handlers.append(console_handler)
        
        # File handler if specified
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(
                logging.Formatter(self.format, self.date_format)
            )
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=self.get_log_level(),
            handlers=handlers,
            force=True
        )