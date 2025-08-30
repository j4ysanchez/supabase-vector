# Supabase Storage Adapter

This package contains the Supabase implementation of the `StoragePort` interface for document storage and retrieval.

## Components

### SupabaseStorageAdapter

The main adapter class that implements the `StoragePort` interface using Supabase as the backend storage system.

**Features:**
- Document storage with chunking support
- Vector embedding storage
- Content hash-based duplicate detection
- Retry logic with exponential backoff
- Comprehensive error handling
- Health check functionality

**Configuration:**
The adapter requires a `SupabaseConfig` instance with the following settings:
- `url`: Supabase project URL
- `service_key`: Supabase service role key
- `table_name`: Database table name (default: "documents")
- `timeout`: Connection timeout in seconds (default: 30)
- `max_retries`: Maximum retry attempts (default: 3)

### Retry Utilities

The `retry_utils.py` module provides a decorator for adding retry logic with exponential backoff to database operations.

**Features:**
- Configurable retry attempts
- Exponential backoff with jitter
- Maximum delay limits
- Comprehensive error logging

## Usage Example

```python
from src.adapters.secondary.supabase import SupabaseStorageAdapter
from src.config import get_supabase_config
from src.domain.models import Document, DocumentChunk

# Create configuration
config = SupabaseConfig(
    url="https://your-project.supabase.co",
    service_key="your-service-key",
    table_name="documents"
)

# Create adapter
storage = SupabaseStorageAdapter(config)

# Create a document
document = Document(
    filename="example.txt",
    file_path=Path("/path/to/example.txt"),
    content_hash="abc123",
    chunks=[
        DocumentChunk(
            content="Document content",
            chunk_index=0,
            embedding=[0.1, 0.2, 0.3]
        )
    ]
)

# Store the document
success = await storage.store_document(document)

# Retrieve the document
retrieved = await storage.retrieve_document(document.id)

# Find by content hash
found = await storage.find_by_hash("abc123")

# List documents
documents = await storage.list_documents(limit=10)

# Delete document
deleted = await storage.delete_document(document.id)

# Health check
healthy = await storage.health_check()
```

## Database Schema

The adapter expects a Supabase table with the following structure:

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON documents (document_id);
CREATE INDEX ON documents (content_hash);
CREATE INDEX ON documents (filename);
```

## Error Handling

The adapter provides comprehensive error handling:

- **StorageError**: Raised for storage-related failures
- **Retry Logic**: Automatic retry with exponential backoff for transient errors
- **Validation**: Configuration validation before operations
- **Logging**: Detailed logging for debugging and monitoring

## Testing

The package includes comprehensive unit and integration tests:

- Unit tests: `tests/unit/adapters/test_supabase_storage_adapter.py`
- Integration tests: `tests/integration/test_storage_integration.py`
- Demo script: `examples/storage_demo.py`

Run tests with:
```bash
python -m pytest tests/unit/adapters/test_supabase_storage_adapter.py
python -m pytest tests/integration/test_storage_integration.py
```

## Mock Implementation

For development and testing, the adapter includes a `MockSupabaseClient` that simulates Supabase operations using in-memory storage. This allows for testing without requiring an actual Supabase instance.

## Requirements

- Python 3.8+
- Supabase Python client (when using real Supabase)
- Vector extension enabled in Supabase database
- Proper database schema and indexes