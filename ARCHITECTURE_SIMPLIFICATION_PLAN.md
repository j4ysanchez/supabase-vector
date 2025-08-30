# Hexagonal Architecture Simplification Plan

## Current Structure (Over-engineered)
```
src/
├── adapters/
│   └── secondary/
│       ├── ollama/ollama_embedding_adapter.py    # 200+ lines
│       └── supabase/supabase_storage_adapter.py  # 300+ lines
├── domain/
│   ├── models/document.py                        # Complex dataclasses
│   └── exceptions.py                             # Custom exception hierarchy
├── ports/
│   └── secondary/
│       ├── embedding_port.py                     # Abstract interfaces
│       └── storage_port.py                       # Abstract interfaces
└── config.py                                     # ✅ Already simplified
```

## Target Structure (Simplified)
```
vector_db/
├── __init__.py
├── cli.py              # Click CLI commands
├── config.py           # ✅ Already simplified (keep as-is)
├── embedding.py        # Direct Ollama client (~50 lines)
├── storage.py          # Direct Supabase client (~80 lines)
├── models.py           # Simple dataclasses (~30 lines)
└── main.py             # Main application logic (~100 lines)
```

## Phase 1: Create New Simplified Files

### 1.1 Create `vector_db/models.py`
```python
"""Simple document models."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

@dataclass
class Document:
    """Simple document representation."""
    filename: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
```

### 1.2 Create `vector_db/embedding.py`
```python
"""Direct Ollama embedding client."""
import httpx
import asyncio
from typing import List
from .config import get_config

class EmbeddingClient:
    def __init__(self):
        config = get_config()
        self.base_url = config.ollama_url
        self.model = config.ollama_model
        self.timeout = config.ollama_timeout
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        tasks = [self.generate_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)
```

### 1.3 Create `vector_db/storage.py`
```python
"""Direct Supabase storage client."""
from supabase import create_client
from typing import List, Optional
from uuid import UUID, uuid4
from .config import get_config
from .models import Document

class StorageClient:
    def __init__(self):
        config = get_config()
        self.client = create_client(config.supabase_url, config.supabase_key)
        self.table = config.supabase_table
    
    def store_document(self, doc: Document) -> UUID:
        """Store document and return its ID."""
        doc_id = uuid4()
        data = {
            "id": str(doc_id),
            "filename": doc.filename,
            "content": doc.content,
            "embedding": doc.embedding,
            "metadata": doc.metadata
        }
        self.client.table(self.table).insert(data).execute()
        return doc_id
    
    def get_document(self, doc_id: UUID) -> Optional[Document]:
        """Retrieve document by ID."""
        result = self.client.table(self.table).select("*").eq("id", str(doc_id)).execute()
        if not result.data:
            return None
        
        data = result.data[0]
        return Document(
            filename=data["filename"],
            content=data["content"],
            embedding=data["embedding"],
            metadata=data.get("metadata", {}),
            id=UUID(data["id"])
        )
    
    def list_documents(self, limit: int = 100) -> List[Document]:
        """List all documents."""
        result = self.client.table(self.table).select("*").limit(limit).execute()
        return [
            Document(
                filename=data["filename"],
                content=data["content"],
                embedding=data["embedding"],
                metadata=data.get("metadata", {}),
                id=UUID(data["id"])
            )
            for data in result.data
        ]
```

### 1.4 Create `vector_db/main.py`
```python
"""Main application logic."""
import asyncio
from pathlib import Path
from typing import List
from .config import get_config
from .models import Document
from .embedding import EmbeddingClient
from .storage import StorageClient

class VectorDB:
    """Simple vector database implementation."""
    
    def __init__(self):
        self.config = get_config()
        self.embedding_client = EmbeddingClient()
        self.storage_client = StorageClient()
    
    async def ingest_file(self, file_path: Path) -> str:
        """Ingest a file into the vector database."""
        # Read file
        content = file_path.read_text(encoding='utf-8')
        
        # Generate embedding
        embedding = await self.embedding_client.generate_embedding(content)
        
        # Create document
        doc = Document(
            filename=file_path.name,
            content=content,
            embedding=embedding
        )
        
        # Store document
        doc_id = self.storage_client.store_document(doc)
        return f"Stored document {file_path.name} with ID: {doc_id}"
    
    def search_similar(self, query: str, limit: int = 5) -> List[Document]:
        """Search for similar documents (simplified version)."""
        # For now, just return all documents
        # In a real implementation, you'd use vector similarity
        return self.storage_client.list_documents(limit=limit)
```

### 1.5 Create `vector_db/cli.py`
```python
"""CLI interface using Click."""
import click
import asyncio
from pathlib import Path
from .main import VectorDB

@click.group()
def cli():
    """Vector Database CLI."""
    pass

@cli.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
def ingest(file_path: Path):
    """Ingest a file into the vector database."""
    db = VectorDB()
    result = asyncio.run(db.ingest_file(file_path))
    click.echo(result)

@cli.command()
@click.argument('query')
@click.option('--limit', default=5, help='Number of results to return')
def search(query: str, limit: int):
    """Search for similar documents."""
    db = VectorDB()
    results = db.search_similar(query, limit)
    
    click.echo(f"Found {len(results)} documents:")
    for doc in results:
        click.echo(f"- {doc.filename}")

@cli.command()
def list():
    """List all documents."""
    db = VectorDB()
    docs = db.storage_client.list_documents()
    
    click.echo(f"Found {len(docs)} documents:")
    for doc in docs:
        click.echo(f"- {doc.filename} (ID: {doc.id})")

if __name__ == '__main__':
    cli()
```

## Phase 2: Migration Steps

### 2.1 Create New Directory Structure
```bash
mkdir vector_db
touch vector_db/__init__.py
```

### 2.2 Copy and Adapt Configuration
```bash
cp src/config.py vector_db/config.py
# Keep the simplified config as-is
```

### 2.3 Update Tests
- Move tests to test the new simplified structure
- Remove adapter-specific tests
- Focus on end-to-end functionality tests

### 2.4 Update Examples
- Simplify examples to use the new direct approach
- Remove complex adapter instantiation

## Phase 3: Remove Old Structure

### 3.1 Files to Delete
```bash
rm -rf src/adapters/
rm -rf src/ports/
rm -rf src/domain/
```

### 3.2 Files to Keep (temporarily)
- Keep old structure until new one is tested
- Gradually migrate functionality

## Benefits of Simplification

### Code Reduction
| Component | Current LOC | New LOC | Reduction |
|-----------|-------------|---------|-----------|
| Adapters | ~500 lines | ~130 lines | 74% |
| Ports | ~100 lines | 0 lines | 100% |
| Domain | ~80 lines | ~30 lines | 62% |
| **Total** | **~680 lines** | **~160 lines** | **76%** |

### Complexity Reduction
- **No more interfaces**: Direct implementation
- **No more dependency injection**: Simple instantiation
- **No more adapter pattern**: Direct service calls
- **Simpler error handling**: Standard exceptions
- **Easier testing**: Test actual functionality, not abstractions

### Development Speed
- **Faster feature development**: No need to update interfaces
- **Easier debugging**: Direct call stack
- **Simpler onboarding**: Less architectural concepts to learn
- **Reduced maintenance**: Fewer files to maintain

## When This Simplification Makes Sense

✅ **Good for**:
- Single database backend (Supabase)
- Single embedding provider (Ollama)
- Small team (1-3 developers)
- Simple CLI tool
- Rapid prototyping

❌ **Not good for**:
- Multiple database backends needed
- Multiple embedding providers
- Large team with strict separation of concerns
- Complex business logic
- Enterprise requirements

## Implementation Timeline

- **Day 1**: Create new simplified structure
- **Day 2**: Migrate core functionality
- **Day 3**: Update tests and examples
- **Day 4**: Remove old structure
- **Day 5**: Documentation and cleanup

## Risk Mitigation

1. **Keep old structure** until new one is fully tested
2. **Migrate tests first** to ensure functionality is preserved
3. **Use feature flags** to switch between old and new implementations
4. **Gradual migration** - migrate one component at a time