# Configuration Management System

This module provides a comprehensive configuration management system for the Python CLI Vector Database application. It follows a modular design with separate configuration classes for each subsystem.

## Features

- **Environment Variable Loading**: Automatic loading from environment variables
- **`.env` File Support**: Load configuration from `.env` files
- **Validation**: Comprehensive validation of all configuration values
- **Type Safety**: Full type hints and dataclass-based configuration
- **Error Handling**: Clear error messages for configuration issues
- **Defaults**: Sensible defaults for optional settings

## Configuration Classes

### ApplicationConfig
Main configuration class that aggregates all subsystem configurations.

```python
from infrastructure.config import ApplicationConfig

# Load from environment variables
config = ApplicationConfig.from_env()

# Load from specific .env file
config = ApplicationConfig.from_env(Path(".env.production"))
```

### SupabaseConfig
Configuration for Supabase database connection.

**Required Environment Variables:**
- `SUPABASE_URL`: The Supabase project URL
- `SUPABASE_SERVICE_KEY`: The Supabase service role key

**Optional Environment Variables:**
- `SUPABASE_TABLE_NAME`: Table name (default: "documents")
- `SUPABASE_TIMEOUT`: Connection timeout in seconds (default: 30)
- `SUPABASE_MAX_RETRIES`: Maximum retry attempts (default: 3)

### OllamaConfig
Configuration for Ollama embedding service.

**Required Environment Variables:**
- `OLLAMA_BASE_URL`: The Ollama service base URL

**Optional Environment Variables:**
- `OLLAMA_MODEL_NAME`: Model name (default: "nomic-embed-text")
- `OLLAMA_TIMEOUT`: Request timeout in seconds (default: 60)
- `OLLAMA_MAX_RETRIES`: Maximum retry attempts (default: 3)
- `OLLAMA_BATCH_SIZE`: Batch size for requests (default: 32)

### ProcessingConfig
Configuration for document processing.

**Optional Environment Variables:**
- `PROCESSING_CHUNK_SIZE`: Chunk size in characters (default: 1000)
- `PROCESSING_CHUNK_OVERLAP`: Overlap between chunks (default: 200)
- `PROCESSING_MAX_FILE_SIZE_MB`: Maximum file size in MB (default: 100)
- `PROCESSING_SUPPORTED_EXTENSIONS`: Comma-separated extensions (default: ".txt")

### LoggingConfig
Configuration for application logging.

**Optional Environment Variables:**
- `LOG_LEVEL`: Logging level (default: "INFO")
- `LOG_FORMAT`: Log message format (default: standard format)
- `LOG_DATE_FORMAT`: Date format (default: "%Y-%m-%d %H:%M:%S")
- `LOG_FILE`: Path to log file (default: None, console only)

## Usage Examples

### Basic Usage
```python
from infrastructure.config import ApplicationConfig, ConfigValidationError

try:
    config = ApplicationConfig.from_env()
    
    # Configure logging
    config.setup_logging()
    
    # Access configuration values
    print(f"Supabase URL: {config.supabase.url}")
    print(f"Ollama Model: {config.ollama.model_name}")
    
except ConfigValidationError as e:
    print(f"Configuration error: {e}")
    print(config.print_config_help())
```

### Using .env Files
```python
from pathlib import Path
from infrastructure.config import ApplicationConfig

# Load from specific .env file
config = ApplicationConfig.from_env(Path(".env.production"))

# Load from default .env file (if it exists)
config = ApplicationConfig.from_env()
```

### Configuration Help
```python
config = ApplicationConfig.from_env()
help_text = config.print_config_help()
print(help_text)
```

## Error Handling

The configuration system provides detailed error messages for common issues:

- Missing required environment variables
- Invalid URL formats
- Invalid numeric values
- Invalid log levels
- File not found errors for .env files

All configuration errors are wrapped in `ConfigValidationError` with descriptive messages.

## Testing

The configuration system includes comprehensive validation and can be tested with the provided test scripts:

```bash
# Test basic configuration functionality
python test_config.py

# Test .env file loading
python test_env_file.py
```

## Example .env File

See `.env.example` for a complete example of all available configuration options.