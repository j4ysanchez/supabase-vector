# Design Document

## Overview

The Python CLI Vector Database application is designed as a modular system that ingests text documents, generates embeddings using Ollama's nomic-embed-text model, and stores them in Supabase's vector database. The architecture follows a clean separation of concerns with distinct layers for CLI interface, business logic, data access, and external service integration.

## Architecture

The application follows a **Ports and Adapters (Hexagonal) Architecture** pattern to ensure maximum flexibility and testability:

```
                    ┌─────────────────────────────────────┐
                    │            Adapters                 │
                    │  ┌─────────────┐ ┌─────────────┐    │
                    │  │ CLI Adapter │ │ Web Adapter │    │
                    │  │  (Click)    │ │  (Future)   │    │
                    │  └─────────────┘ └─────────────┘    │
                    └─────────────┬───────────────────────┘
                                  │ Primary Ports
                    ┌─────────────▼───────────────────────┐
                    │         Application Core            │
                    │                                     │
                    │  ┌─────────────────────────────┐    │
                    │  │    Domain Services          │    │
                    │  │  - DocumentProcessor        │    │
                    │  │  - EmbeddingOrchestrator    │    │
                    │  └─────────────────────────────┘    │
                    │                                     │
                    │  ┌─────────────────────────────┐    │
                    │  │      Domain Models          │    │
                    │  │  - Document, Chunk, etc.    │    │
                    │  └─────────────────────────────┘    │
                    └─────────────┬───────────────────────┘
                                  │ Secondary Ports
                    ┌─────────────▼───────────────────────┐
                    │            Adapters                 │
                    │  ┌─────────────┐ ┌─────────────┐    │
                    │  │  Supabase   │ │   Ollama    │    │
                    │  │   Adapter   │ │   Adapter   │    │
                    │  └─────────────┘ └─────────────┘    │
                    │  ┌─────────────┐ ┌─────────────┐    │
                    │  │ File System │ │   Future    │    │
                    │  │   Adapter   │ │  Adapters   │    │
                    │  └─────────────┘ └─────────────┘    │
                    └─────────────────────────────────────┘
```

### Key Design Principles

- **Ports and Adapters**: Core business logic isolated from external concerns through well-defined interfaces
- **Dependency Inversion**: Core depends on abstractions, not concrete implementations
- **Single Responsibility**: Each adapter handles one external concern
- **Open/Closed**: Easy to add new adapters without modifying core logic
- **Testability**: Core logic can be tested in isolation with mock adapters
- **Configuration-Driven**: All external dependencies configurable via environment variables
- **Error Resilience**: Comprehensive error handling with retry mechanisms
- **Batch Processing**: Efficient handling of multiple documents

## Components and Interfaces

### Core Domain (`domain/`)

**Domain Models** (`domain/models/`)
```python
@dataclass
class Document:
    id: Optional[UUID]
    filename: str
    file_path: Path
    content_hash: str
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any]
    created_at: Optional[datetime] = None

@dataclass
class DocumentChunk:
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessingResult:
    document: Document
    success: bool
    chunks_processed: int
    error_message: Optional[str] = None
```

**Domain Services** (`domain/services/`)
```python
class DocumentProcessor:
    def __init__(self, chunker: TextChunker, hasher: ContentHasher):
        self._chunker = chunker
        self._hasher = hasher
    
    def process_document(self, file_path: Path, content: str) -> Document:
        # Pure business logic for document processing

class EmbeddingOrchestrator:
    def __init__(self, embedding_port: EmbeddingPort, storage_port: StoragePort):
        self._embedding_port = embedding_port
        self._storage_port = storage_port
    
    async def process_and_store(self, document: Document) -> ProcessingResult:
        # Orchestrates embedding generation and storage
```

### Primary Ports (`ports/primary/`)

**Application Service Interface**
```python
class DocumentIngestionPort(ABC):
    @abstractmethod
    async def ingest_file(self, file_path: Path) -> ProcessingResult:
        pass
    
    @abstractmethod
    async def ingest_directory(self, dir_path: Path) -> List[ProcessingResult]:
        pass
    
    @abstractmethod
    async def check_health(self) -> HealthStatus:
        pass
```

### Secondary Ports (`ports/secondary/`)

**Storage Port**
```python
class StoragePort(ABC):
    @abstractmethod
    async def store_document(self, document: Document) -> bool:
        pass
    
    @abstractmethod
    async def find_by_hash(self, content_hash: str) -> Optional[Document]:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass
```

**Embedding Port**
```python
class EmbeddingPort(ABC):
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass
```

**File System Port**
```python
class FileSystemPort(ABC):
    @abstractmethod
    def read_file(self, file_path: Path) -> str:
        pass
    
    @abstractmethod
    def list_text_files(self, dir_path: Path) -> List[Path]:
        pass
```

### Primary Adapters (`adapters/primary/`)

**CLI Adapter** (`adapters/primary/cli/`)
```python
class CLIAdapter:
    def __init__(self, ingestion_service: DocumentIngestionPort):
        self._ingestion_service = ingestion_service
    
    # Click commands that delegate to the application service
```

**Future Web Adapter** (`adapters/primary/web/`)
- FastAPI or Flask adapter for HTTP interface
- GraphQL adapter for flexible querying
- gRPC adapter for high-performance scenarios

### Secondary Adapters (`adapters/secondary/`)

**Supabase Adapter** (`adapters/secondary/supabase/`)
```python
class SupabaseStorageAdapter(StoragePort):
    def __init__(self, client: Client, config: SupabaseConfig):
        self._client = client
        self._config = config
    
    async def store_document(self, document: Document) -> bool:
        # Implementation specific to Supabase
```

**Ollama Adapter** (`adapters/secondary/ollama/`)
```python
class OllamaEmbeddingAdapter(EmbeddingPort):
    def __init__(self, client: httpx.AsyncClient, config: OllamaConfig):
        self._client = client
        self._config = config
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Implementation specific to Ollama API
```

**File System Adapter** (`adapters/secondary/filesystem/`)
```python
class LocalFileSystemAdapter(FileSystemPort):
    def read_file(self, file_path: Path) -> str:
        # Standard file system operations
```

**Future Adapters**
- **PostgreSQL with pgvector**: Alternative to Supabase
- **OpenAI Embeddings**: Alternative to Ollama
- **Weaviate/Pinecone**: Alternative vector databases
- **S3/MinIO**: For document storage
- **Redis**: For caching embeddings

### Application Services (`application/`)

**Document Ingestion Service** (`application/services/`)
```python
class DocumentIngestionService(DocumentIngestionPort):
    def __init__(
        self,
        document_processor: DocumentProcessor,
        embedding_orchestrator: EmbeddingOrchestrator,
        file_system: FileSystemPort
    ):
        # Implements the primary port using domain services
```

### Configuration and Dependency Injection (`infrastructure/`)

**Configuration** (`infrastructure/config/`)
```python
@dataclass
class ApplicationConfig:
    supabase: SupabaseConfig
    ollama: OllamaConfig
    processing: ProcessingConfig
    logging: LoggingConfig

class DIContainer:
    def __init__(self, config: ApplicationConfig):
        self._config = config
        self._setup_dependencies()
    
    def get_ingestion_service(self) -> DocumentIngestionPort:
        # Wire up all dependencies
```

### Database Schema

**Supabase Schema**:
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON documents (filename);
CREATE INDEX ON documents (content_hash);
```

## Data Models

### Document Storage Model

Each document chunk is stored with the following structure:
- **id**: Unique identifier (UUID)
- **filename**: Original filename
- **file_path**: Full path to source file
- **content_hash**: SHA-256 hash for duplicate detection
- **chunk_index**: Position within the original document
- **content**: Text content of the chunk
- **embedding**: Vector representation (768 dimensions for nomic-embed-text)
- **metadata**: Additional information (file size, processing timestamp, etc.)

### Configuration Model

Environment-based configuration with validation:
- **Database**: Supabase URL and service key
- **Embedding**: Ollama endpoint and model selection
- **Processing**: Chunk size, overlap, and batch settings
- **Logging**: Level and output configuration

## Error Handling

### Error Categories

1. **Configuration Errors**: Missing or invalid environment variables
2. **File System Errors**: Unreadable files, permission issues
3. **Network Errors**: Ollama or Supabase connectivity issues
4. **Processing Errors**: Embedding generation failures
5. **Database Errors**: Storage and retrieval failures

### Error Handling Strategy

- **Graceful Degradation**: Continue processing other files when individual files fail
- **Retry Logic**: Exponential backoff for transient network errors
- **User Feedback**: Clear error messages with actionable suggestions
- **Logging**: Comprehensive logging for debugging and monitoring

### Retry Configuration

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
```

## Testing Strategy

### Unit Testing
- **Service Layer**: Mock external dependencies (Ollama, Supabase)
- **Repository Layer**: Use test database or mocking
- **Configuration**: Test validation and error cases
- **Document Processing**: Test chunking logic and edge cases

### Integration Testing
- **End-to-End**: Test complete ingestion workflow
- **Database**: Test actual Supabase operations with test data
- **API Integration**: Test Ollama connectivity and embedding generation

### Test Structure
```
tests/
├── unit/
│   ├── domain/
│   │   ├── test_document_processor.py
│   │   └── test_embedding_orchestrator.py
│   ├── application/
│   │   └── test_document_ingestion_service.py
│   └── adapters/
│       ├── test_supabase_adapter.py
│       ├── test_ollama_adapter.py
│       └── test_filesystem_adapter.py
├── integration/
│   ├── test_cli_adapter.py
│   └── test_full_workflow.py
├── fixtures/
│   └── sample_documents/
└── mocks/
    ├── mock_embedding_port.py
    ├── mock_storage_port.py
    └── mock_filesystem_port.py
```

### Performance Testing
- **Batch Processing**: Verify efficient handling of multiple documents
- **Memory Usage**: Monitor memory consumption during large file processing
- **Database Performance**: Test vector similarity search performance

## Security Considerations

### API Key Management
- Store sensitive credentials in environment variables
- Support for .env files in development
- Clear documentation for production deployment

### Input Validation
- Validate file paths to prevent directory traversal
- Sanitize file content before processing
- Limit file sizes to prevent resource exhaustion

### Database Security
- Use Supabase Row Level Security (RLS) policies
- Implement proper authentication for database access
- Validate all database inputs to prevent injection attacks