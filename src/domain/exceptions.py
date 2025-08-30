"""Domain exceptions for the application."""


class DomainError(Exception):
    """Base exception for domain-related errors."""
    pass


class StorageError(DomainError):
    """Exception raised for storage-related errors."""
    
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class ConfigurationError(DomainError):
    """Exception raised for configuration-related errors."""
    pass


class ProcessingError(DomainError):
    """Exception raised for document processing errors."""
    pass


class EmbeddingError(DomainError):
    """Exception raised for embedding generation errors."""
    
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error