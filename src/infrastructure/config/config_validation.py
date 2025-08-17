"""Configuration validation utilities."""


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    
    def __init__(self, message: str, field: str = None):
        """Initialize configuration validation error.
        
        Args:
            message: Error message describing the validation failure
            field: Optional field name that failed validation
        """
        self.field = field
        super().__init__(message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.field:
            return f"Configuration error in field '{self.field}': {super().__str__()}"
        return f"Configuration error: {super().__str__()}"