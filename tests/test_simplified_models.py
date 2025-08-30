"""
Unit tests for the simplified dataclass models.
"""
import pytest
from datetime import datetime

# Import the models directly to avoid conftest conflicts
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from vector_db.models import Document, DocumentChunk, ProcessingResult


@pytest.mark.unit
def test_document_chunk_creation():
    """Test DocumentChunk creation with required fields."""
    chunk = DocumentChunk(
        content="This is a test chunk",
        chunk_index=0
    )
    
    assert chunk.content == "This is a test chunk"
    assert chunk.chunk_index == 0
    assert chunk.embedding is None
    assert chunk.metadata == {}


@pytest.mark.unit
def test_document_chunk_with_embedding():
    """Test DocumentChunk creation with embedding."""
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    chunk = DocumentChunk(
        content="Test content",
        chunk_index=1,
        embedding=embedding
    )
    
    assert chunk.content == "Test content"
    assert chunk.chunk_index == 1
    assert chunk.embedding == embedding
    assert len(chunk.embedding) == 5


@pytest.mark.unit
def test_document_chunk_with_metadata():
    """Test DocumentChunk creation with metadata."""
    metadata = {"source": "test.txt", "chunk_size": 100}
    chunk = DocumentChunk(
        content="Test content",
        chunk_index=2,
        metadata=metadata
    )
    
    assert chunk.content == "Test content"
    assert chunk.chunk_index == 2
    assert chunk.metadata == metadata
    assert chunk.metadata["source"] == "test.txt"
    assert chunk.metadata["chunk_size"] == 100


@pytest.mark.unit
def test_document_creation():
    """Test Document creation with required fields."""
    document = Document(
        filename="test.txt",
        file_path="/path/to/test.txt",
        content_hash="abc123"
    )
    
    assert document.filename == "test.txt"
    assert document.file_path == "/path/to/test.txt"
    assert document.content_hash == "abc123"
    assert document.chunks == []
    assert document.metadata == {}
    assert document.created_at is None


@pytest.mark.unit
def test_document_with_chunks():
    """Test Document creation with chunks."""
    chunk1 = DocumentChunk(content="First chunk", chunk_index=0)
    chunk2 = DocumentChunk(content="Second chunk", chunk_index=1)
    chunks = [chunk1, chunk2]
    
    document = Document(
        filename="test.txt",
        file_path="/path/to/test.txt",
        content_hash="abc123",
        chunks=chunks
    )
    
    assert len(document.chunks) == 2
    assert document.chunks[0].content == "First chunk"
    assert document.chunks[1].content == "Second chunk"
    assert document.chunks[0].chunk_index == 0
    assert document.chunks[1].chunk_index == 1


@pytest.mark.unit
def test_document_with_metadata():
    """Test Document creation with metadata."""
    metadata = {"file_size": 1024, "encoding": "utf-8"}
    created_at = datetime.now()
    
    document = Document(
        filename="test.txt",
        file_path="/path/to/test.txt",
        content_hash="abc123",
        metadata=metadata,
        created_at=created_at
    )
    
    assert document.metadata == metadata
    assert document.metadata["file_size"] == 1024
    assert document.metadata["encoding"] == "utf-8"
    assert document.created_at == created_at


@pytest.mark.unit
def test_document_complex_structure():
    """Test Document with complex chunk structure."""
    chunks = []
    for i in range(3):
        chunk = DocumentChunk(
            content=f"Chunk {i} content",
            chunk_index=i,
            embedding=[0.1 * i, 0.2 * i, 0.3 * i],
            metadata={"chunk_length": len(f"Chunk {i} content")}
        )
        chunks.append(chunk)
    
    document = Document(
        filename="complex.txt",
        file_path="/path/to/complex.txt",
        content_hash="complex123",
        chunks=chunks,
        metadata={"total_chunks": 3, "processing_version": "1.0"}
    )
    
    assert len(document.chunks) == 3
    assert document.metadata["total_chunks"] == 3
    assert document.chunks[0].embedding == [0.0, 0.0, 0.0]
    assert document.chunks[1].embedding == [0.1, 0.2, 0.3]
    assert document.chunks[2].embedding == [0.2, 0.4, 0.6]


@pytest.mark.unit
def test_processing_result_success():
    """Test ProcessingResult for successful processing."""
    result = ProcessingResult(
        filename="test.txt",
        success=True,
        chunks_processed=5,
        processing_time=2.5
    )
    
    assert result.filename == "test.txt"
    assert result.success is True
    assert result.chunks_processed == 5
    assert result.error_message is None
    assert result.processing_time == 2.5


@pytest.mark.unit
def test_processing_result_failure():
    """Test ProcessingResult for failed processing."""
    result = ProcessingResult(
        filename="error.txt",
        success=False,
        error_message="File not found",
        processing_time=0.1
    )
    
    assert result.filename == "error.txt"
    assert result.success is False
    assert result.chunks_processed == 0  # Default value
    assert result.error_message == "File not found"
    assert result.processing_time == 0.1


@pytest.mark.unit
def test_processing_result_defaults():
    """Test ProcessingResult with default values."""
    result = ProcessingResult(
        filename="minimal.txt",
        success=True
    )
    
    assert result.filename == "minimal.txt"
    assert result.success is True
    assert result.chunks_processed == 0
    assert result.error_message is None
    assert result.processing_time == 0.0


@pytest.mark.unit
def test_models_are_dataclasses():
    """Test that all models are proper dataclasses."""
    # Test that they have the dataclass attributes
    assert hasattr(DocumentChunk, '__dataclass_fields__')
    assert hasattr(Document, '__dataclass_fields__')
    assert hasattr(ProcessingResult, '__dataclass_fields__')
    
    # Test field names
    chunk_fields = set(DocumentChunk.__dataclass_fields__.keys())
    expected_chunk_fields = {'content', 'chunk_index', 'embedding', 'metadata'}
    assert chunk_fields == expected_chunk_fields
    
    document_fields = set(Document.__dataclass_fields__.keys())
    expected_document_fields = {'filename', 'file_path', 'content_hash', 'chunks', 'metadata', 'created_at', 'content', 'embedding', 'id'}
    assert document_fields == expected_document_fields
    
    result_fields = set(ProcessingResult.__dataclass_fields__.keys())
    expected_result_fields = {'filename', 'success', 'chunks_processed', 'error_message', 'processing_time'}
    assert result_fields == expected_result_fields


@pytest.mark.unit
def test_models_immutability():
    """Test that models can be modified (they are mutable dataclasses)."""
    chunk = DocumentChunk(content="Test", chunk_index=0)
    
    # Should be able to modify fields
    chunk.embedding = [0.1, 0.2, 0.3]
    assert chunk.embedding == [0.1, 0.2, 0.3]
    
    chunk.metadata["new_key"] = "new_value"
    assert chunk.metadata["new_key"] == "new_value"


@pytest.mark.unit
def test_document_chunk_types():
    """Test DocumentChunk type annotations work correctly."""
    chunk = DocumentChunk(
        content="Test content",
        chunk_index=0,
        embedding=[1.0, 2.0, 3.0],
        metadata={"key": "value"}
    )
    
    # Test types
    assert isinstance(chunk.content, str)
    assert isinstance(chunk.chunk_index, int)
    assert isinstance(chunk.embedding, list)
    assert isinstance(chunk.metadata, dict)
    assert all(isinstance(x, float) for x in chunk.embedding)


@pytest.mark.unit
def test_document_types():
    """Test Document type annotations work correctly."""
    chunk = DocumentChunk(content="Test", chunk_index=0)
    document = Document(
        filename="test.txt",
        file_path="/path/test.txt",
        content_hash="hash123",
        chunks=[chunk],
        metadata={"size": 100},
        created_at=datetime.now()
    )
    
    # Test types
    assert isinstance(document.filename, str)
    assert isinstance(document.file_path, str)
    assert isinstance(document.content_hash, str)
    assert isinstance(document.chunks, list)
    assert isinstance(document.metadata, dict)
    assert isinstance(document.created_at, datetime)
    assert all(isinstance(c, DocumentChunk) for c in document.chunks)