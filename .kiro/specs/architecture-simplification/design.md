# Design Document

## Overview

The architecture simplification transforms the over-engineered hexagonal architecture into a straightforward, maintainable CLI application. The design eliminates unnecessary abstraction layers while preserving all functionality, reducing code complexity by 70-80%. The simplified architecture uses direct service implementations, a flat module structure, and consolidated configuration management.

## Architecture

### Current Complex Architecture (To Be Simplified)
```
src/
├── adapters/
│   ├── primary/cli/          # CLI adapter layer
│   └── secondary/            # Storage/embedding adapters
│       ├── supabase/
│       └── ollama/
├── application/
│   └── services/             # Application service layer
├── domain/
│   ├── models/               # Domain models
│   └── services/             # Domain services
├── infrastructure/
│   ├── config/               # Complex config system
│   └── di/                   # Dependency injection
└── ports/
    ├── primary/              # Primary port interfaces
    └── secondary/            # Secondary port interfaces
```

### New Simplified Architecture
```
vector_db/
├── __init__.py               # Package initialization
├── cli.py                    # Click CLI commands (direct implementation)
├── config.py                 # Single Pydantic configuration class
├── embedding.py              # Direct Ollama client wrapper
├── storage.py                # Direct Supabase client wrapper
├── models.py                 # Simple dataclasses
└── main.py                   # Main application logic and orchestration
```

### Architecture Comparison

| Aspect | Current (Complex) | Simplified | Reduction |
|--------|------------------|------------|-----------|
| Files | ~25 Python files | ~6 Python files | 76% |
| Abstraction Layers | 4 layers (CLI→App→Domain→Adapters) | 2 layers (CLI→Services) | 50% |
| Interfaces | 6+ abstract interfaces | 0 abstract interfaces | 100% |
| Config Classes | 6 separate classes | 1 Pydantic class | 83% |
| Lines of Code | ~3800 lines | ~850 lines | 78% |

## Components and Interfaces

### Core Module Structure

**1. Configuration (`config.py`)**
```python
from pydantic import BaseSettings, validator
from typing import Optional

class Config(BaseSettings):
    # Supabase Configuration
    supabase_url: str
    supabase_key: str
    supabase_table: str = "documents"
    
    # Ollama Configuration  
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "nomic-embed-text"
    
    # Processing Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size: int = 10_000_000  # 10MB
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    
    @validator('supabase_url')
    def validate_supabase_url(cls, v):
        if not v.startswith('https://'):
            raise ValueError('Supabase URL must start with https://')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Global config instance
config = Config()
```

**2. Data Models (`models.py`)**
```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

@dataclass
class DocumentChunk:
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Document:
    filename: str
    file_path: str
    content_hash: str
    chunks: List[DocumentChunk] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

@dataclass
class ProcessingResult:
    filename: str
    success: bool
    chunks_processed: int = 0
    error_message: Optional[str] = None
    processing_time: float = 0.0
```

**3. Embedding Service (`embedding.py`)**
```python
import httpx
import asyncio
from typing import List
from .config import config
from .models import DocumentChunk

class EmbeddingService:
    def __init__(self):
        self.base_url = config.ollama_url
        self.model = config.ollama_model
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        tasks = [self.generate_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    async def process_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Add embeddings to document chunks."""
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.generate_embeddings_batch(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        return chunks
    
    async def health_check(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
```

**4. Storage Service (`storage.py`)**
```python
from supabase import create_client, Client
from typing import List, Optional
import json
from .config import config
from .models import Document, DocumentChunk

class StorageService:
    def __init__(self):
        self.client: Client = create_client(config.supabase_url, config.supabase_key)
        self.table_name = config.supabase_table
    
    async def store_document(self, document: Document) -> bool:
        """Store document chunks in Supabase."""
        try:
            # Prepare data for insertion
            rows = []
            for chunk in document.chunks:
                row = {
                    "filename": document.filename,
                    "file_path": document.file_path,
                    "content_hash": document.content_hash,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding": chunk.embedding,
                    "metadata": {
                        **document.metadata,
                        **chunk.metadata
                    }
                }
                rows.append(row)
            
            # Insert all chunks in a single batch
            result = self.client.table(self.table_name).insert(rows).execute()
            return len(result.data) == len(rows)
            
        except Exception as e:
            raise RuntimeError(f"Failed to store document: {e}")
    
    def find_by_hash(self, content_hash: str) -> Optional[Document]:
        """Find document by content hash."""
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("content_hash", content_hash)\
                .execute()
            
            if not result.data:
                return None
            
            # Reconstruct document from chunks
            chunks = []
            for row in result.data:
                chunk = DocumentChunk(
                    content=row["content"],
                    chunk_index=row["chunk_index"],
                    embedding=row["embedding"],
                    metadata=row.get("metadata", {})
                )
                chunks.append(chunk)
            
            # Sort chunks by index
            chunks.sort(key=lambda x: x.chunk_index)
            
            first_row = result.data[0]
            return Document(
                filename=first_row["filename"],
                file_path=first_row["file_path"],
                content_hash=content_hash,
                chunks=chunks,
                created_at=first_row.get("created_at")
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to find document: {e}")
    
    def health_check(self) -> bool:
        """Check if Supabase connection is working."""
        try:
            result = self.client.table(self.table_name).select("id").limit(1).execute()
            return True
        except:
            return False
```

**5. Main Application Logic (`main.py`)**
```python
import asyncio
import hashlib
from pathlib import Path
from typing import List
import time
from .config import config
from .models import Document, DocumentChunk, ProcessingResult
from .embedding import EmbeddingService
from .storage import StorageService

class VectorDB:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.storage_service = StorageService()
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        chunk_size = config.chunk_size
        overlap = config.chunk_overlap
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end >= len(text):
                break
            
            start = end - overlap
        
        return chunks
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _read_file(self, file_path: Path) -> str:
        """Read file content with error handling."""
        try:
            if file_path.stat().st_size > config.max_file_size:
                raise ValueError(f"File too large: {file_path.stat().st_size} bytes")
            
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with different encoding
            return file_path.read_text(encoding='latin-1')
    
    async def ingest_file(self, file_path: Path) -> ProcessingResult:
        """Ingest a single file into the vector database."""
        start_time = time.time()
        
        try:
            # Read and validate file
            content = self._read_file(file_path)
            content_hash = self._calculate_hash(content)
            
            # Check if already exists
            existing = self.storage_service.find_by_hash(content_hash)
            if existing:
                return ProcessingResult(
                    filename=file_path.name,
                    success=True,
                    chunks_processed=len(existing.chunks),
                    error_message="Document already exists (skipped)"
                )
            
            # Create document chunks
            text_chunks = self._chunk_text(content)
            chunks = [
                DocumentChunk(
                    content=chunk_text,
                    chunk_index=i,
                    metadata={"chunk_size": len(chunk_text)}
                )
                for i, chunk_text in enumerate(text_chunks)
            ]
            
            # Generate embeddings
            chunks_with_embeddings = await self.embedding_service.process_chunks(chunks)
            
            # Create document
            document = Document(
                filename=file_path.name,
                file_path=str(file_path),
                content_hash=content_hash,
                chunks=chunks_with_embeddings,
                metadata={
                    "file_size": file_path.stat().st_size,
                    "total_chunks": len(chunks)
                }
            )
            
            # Store in database
            success = await self.storage_service.store_document(document)
            
            return ProcessingResult(
                filename=file_path.name,
                success=success,
                chunks_processed=len(chunks),
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            return ProcessingResult(
                filename=file_path.name,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    async def ingest_directory(self, dir_path: Path) -> List[ProcessingResult]:
        """Ingest all .txt files in a directory."""
        txt_files = list(dir_path.glob("*.txt"))
        
        if not txt_files:
            return []
        
        tasks = [self.ingest_file(file_path) for file_path in txt_files]
        return await asyncio.gather(*tasks)
    
    async def health_check(self) -> dict:
        """Check health of all services."""
        embedding_healthy = await self.embedding_service.health_check()
        storage_healthy = self.storage_service.health_check()
        
        return {
            "embedding_service": embedding_healthy,
            "storage_service": storage_healthy,
            "overall": embedding_healthy and storage_healthy
        }
    
    async def close(self):
        """Clean up resources."""
        await self.embedding_service.close()
```

**6. CLI Interface (`cli.py`)**
```python
import click
import asyncio
from pathlib import Path
from .main import VectorDB
from .config import config

@click.group()
def cli():
    """Python CLI Vector Database - Ingest documents into Supabase with Ollama embeddings."""
    pass

@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
async def ingest(path: Path, verbose: bool):
    """Ingest a file or directory of .txt files."""
    db = VectorDB()
    
    try:
        if path.is_file():
            if not path.suffix == '.txt':
                click.echo(f"Error: Only .txt files are supported")
                return
            
            result = await db.ingest_file(path)
            if result.success:
                click.echo(f"✓ {result.filename}: {result.chunks_processed} chunks processed")
            else:
                click.echo(f"✗ {result.filename}: {result.error_message}")
        
        elif path.is_dir():
            results = await db.ingest_directory(path)
            
            if not results:
                click.echo("No .txt files found in directory")
                return
            
            successful = sum(1 for r in results if r.success)
            total_chunks = sum(r.chunks_processed for r in results if r.success)
            
            click.echo(f"Processed {successful}/{len(results)} files, {total_chunks} total chunks")
            
            if verbose:
                for result in results:
                    status = "✓" if result.success else "✗"
                    message = f"{result.chunks_processed} chunks" if result.success else result.error_message
                    click.echo(f"  {status} {result.filename}: {message}")
    
    finally:
        await db.close()

@cli.command()
async def status():
    """Check the health of all services."""
    db = VectorDB()
    
    try:
        health = await db.health_check()
        
        click.echo("Service Status:")
        click.echo(f"  Embedding (Ollama): {'✓' if health['embedding_service'] else '✗'}")
        click.echo(f"  Storage (Supabase): {'✓' if health['storage_service'] else '✗'}")
        click.echo(f"  Overall: {'✓ Healthy' if health['overall'] else '✗ Issues detected'}")
        
        if not health['overall']:
            click.echo("\nTroubleshooting:")
            if not health['embedding_service']:
                click.echo(f"  - Check Ollama is running at {config.ollama_url}")
            if not health['storage_service']:
                click.echo(f"  - Check Supabase credentials and connection")
    
    finally:
        await db.close()

@cli.command()
def config_show():
    """Show current configuration."""
    click.echo("Current Configuration:")
    click.echo(f"  Supabase URL: {config.supabase_url}")
    click.echo(f"  Supabase Table: {config.supabase_table}")
    click.echo(f"  Ollama URL: {config.ollama_url}")
    click.echo(f"  Ollama Model: {config.ollama_model}")
    click.echo(f"  Chunk Size: {config.chunk_size}")
    click.echo(f"  Chunk Overlap: {config.chunk_overlap}")

def main():
    """Entry point for the CLI."""
    # Convert async commands to sync
    def async_command(f):
        def wrapper(*args, **kwargs):
            return asyncio.run(f(*args, **kwargs))
        return wrapper
    
    # Apply async wrapper to async commands
    ingest.callback = async_command(ingest.callback)
    status.callback = async_command(status.callback)
    
    cli()

if __name__ == '__main__':
    main()
```

## Data Models

### Simplified Data Structure

The simplified architecture uses straightforward dataclasses instead of complex domain models:

- **Document**: Contains file metadata and list of chunks
- **DocumentChunk**: Contains text content, embedding, and metadata
- **ProcessingResult**: Contains processing outcome and metrics

### Database Schema (Unchanged)

The existing Supabase schema remains the same, ensuring compatibility:

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Error Handling

### Simplified Error Strategy

Instead of complex exception hierarchies, the simplified architecture uses:

1. **Standard Exceptions**: Use built-in Python exceptions with descriptive messages
2. **Result Objects**: Return ProcessingResult objects that contain success/failure information
3. **Graceful Degradation**: Continue processing other files when individual files fail
4. **Clear User Feedback**: Provide actionable error messages through the CLI

### Error Handling Patterns

```python
# Simple error handling with standard exceptions
try:
    result = await self.client.post(url, json=data)
    result.raise_for_status()
    return result.json()
except httpx.RequestError as e:
    raise RuntimeError(f"Network error connecting to Ollama: {e}")
except httpx.HTTPStatusError as e:
    raise RuntimeError(f"Ollama API error: {e.response.status_code}")
```

## Testing Strategy

### Simplified Test Structure

```
tests/
├── test_config.py           # Configuration validation tests
├── test_embedding.py        # Ollama service tests (with mocking)
├── test_storage.py          # Supabase service tests (with mocking)
├── test_main.py            # Main application logic tests
├── test_cli.py             # CLI command tests
├── test_integration.py     # End-to-end integration tests
└── conftest.py             # Shared fixtures and test utilities
```

### Testing Approach

1. **Unit Tests**: Test individual services with mocked dependencies
2. **Integration Tests**: Test complete workflows with real services (optional)
3. **CLI Tests**: Test command-line interface using Click's testing utilities
4. **Mocking Strategy**: Use simple mocks instead of complex adapter mocks

### Example Test Pattern

```python
# Simple mocking approach
@pytest.fixture
def mock_ollama_client(monkeypatch):
    async def mock_post(*args, **kwargs):
        return MockResponse({"embedding": [0.1, 0.2, 0.3]})
    
    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

def test_embedding_generation(mock_ollama_client):
    service = EmbeddingService()
    result = await service.generate_embedding("test text")
    assert result == [0.1, 0.2, 0.3]
```

## Migration Strategy

### Phase 1: Create Simplified Structure
1. Create new `vector_db/` package with simplified modules
2. Implement direct service classes without abstractions
3. Create unified configuration using Pydantic

### Phase 2: Migrate Functionality
1. Move CLI commands to simplified `cli.py`
2. Migrate embedding logic to direct Ollama client
3. Migrate storage logic to direct Supabase client
4. Update main application orchestration

### Phase 3: Update Tests
1. Restructure tests to match new module layout
2. Replace adapter mocks with simple service mocks
3. Update integration tests for simplified architecture

### Phase 4: Clean Up
1. Remove old `src/` directory structure
2. Update documentation and README
3. Verify all functionality works with simplified code

## Benefits of Simplification

1. **Reduced Complexity**: 78% fewer lines of code
2. **Easier Maintenance**: Flat structure is easier to navigate
3. **Faster Development**: Direct implementations are quicker to modify
4. **Better Debugging**: Fewer abstraction layers make issues easier to trace
5. **Improved Onboarding**: New developers can understand the code faster
6. **Less Overhead**: No performance penalty from unnecessary abstractions

The simplified architecture maintains all existing functionality while dramatically reducing complexity, making the codebase more maintainable and easier to understand for a CLI tool of this scope.