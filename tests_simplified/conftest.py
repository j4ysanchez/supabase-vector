"""Pytest configuration and fixtures for simplified tests."""

import asyncio
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from vector_db.main import VectorDB
from vector_db.models import Document
from vector_db.embedding import EmbeddingClient
from vector_db.storage import StorageClient


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document(
        filename="test_document.txt",
        content="This is a test document with some sample content for testing purposes.",
        metadata={"test": True, "source": "pytest"}
    )


@pytest.fixture
def sample_documents():
    """Create multiple sample documents for testing."""
    return [
        Document(
            filename="doc1.txt",
            content="First document about machine learning and AI.",
            metadata={"category": "tech"}
        ),
        Document(
            filename="doc2.txt", 
            content="Second document about data science and analytics.",
            metadata={"category": "data"}
        ),
        Document(
            filename="doc3.txt",
            content="Third document about software engineering practices.",
            metadata={"category": "engineering"}
        )
    ]


@pytest.fixture
def temp_text_file():
    """Create a temporary text file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        content = """
        This is a temporary test file created for testing the vector database.
        It contains multiple lines of text that can be used to test
        file ingestion, embedding generation, and storage functionality.
        
        The file includes various topics like:
        - Machine learning algorithms
        - Data processing techniques  
        - Software development practices
        - Database management systems
        """
        f.write(content.strip())
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_directory():
    """Create a temporary directory with multiple test files."""
    import tempfile
    import shutil
    
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create test files
    files_content = {
        "document1.txt": "First document about artificial intelligence and machine learning.",
        "document2.txt": "Second document about data science and statistical analysis.",
        "document3.md": "# Third Document\n\nThis is a markdown document about software engineering.",
        "document4.py": "# Python code example\nprint('Hello, World!')\n\ndef test_function():\n    return True",
        "README.txt": "This is a README file explaining the test documents."
    }
    
    for filename, content in files_content.items():
        (temp_dir / filename).write_text(content)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_embedding_client():
    """Create a mock embedding client for testing."""
    mock_client = Mock(spec=EmbeddingClient)
    
    # Mock embedding generation
    mock_client.generate_embedding = AsyncMock(return_value=[0.1] * 768)
    mock_client.generate_embeddings = AsyncMock(return_value=[[0.1] * 768, [0.2] * 768])
    mock_client.health_check = AsyncMock(return_value=True)
    
    return mock_client


@pytest.fixture
def mock_storage_client():
    """Create a mock storage client for testing."""
    mock_client = Mock(spec=StorageClient)
    
    # Mock storage operations
    mock_client.store_document = Mock(return_value=uuid4())
    mock_client.get_document = Mock(return_value=None)
    mock_client.list_documents = Mock(return_value=[])
    mock_client.delete_document = Mock(return_value=True)
    mock_client.search_by_content = Mock(return_value=[])
    mock_client.health_check = Mock(return_value=True)
    
    return mock_client


@pytest.fixture
def mock_vector_db(mock_embedding_client, mock_storage_client):
    """Create a VectorDB instance with mocked clients."""
    db = VectorDB()
    db.embedding_client = mock_embedding_client
    db.storage_client = mock_storage_client
    return db


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Test markers
pytest_plugins = []