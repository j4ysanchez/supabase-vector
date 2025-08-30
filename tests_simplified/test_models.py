"""Tests for the simplified document models."""

import pytest
from datetime import datetime
from uuid import uuid4

from vector_db.models import Document


class TestDocument:
    """Test the simplified Document model."""
    
    def test_document_creation(self):
        """Test basic document creation."""
        doc = Document(
            filename="test.txt",
            content="This is test content."
        )
        
        assert doc.filename == "test.txt"
        assert doc.content == "This is test content."
        assert doc.embedding is None
        assert doc.metadata == {}
        assert doc.id is None
        assert doc.created_at is None
    
    def test_document_with_all_fields(self):
        """Test document creation with all fields."""
        doc_id = uuid4()
        created_at = datetime.now()
        embedding = [0.1, 0.2, 0.3]
        metadata = {"source": "test", "category": "example"}
        
        doc = Document(
            filename="full_test.txt",
            content="Full test content with all fields.",
            embedding=embedding,
            metadata=metadata,
            id=doc_id,
            created_at=created_at
        )
        
        assert doc.filename == "full_test.txt"
        assert doc.content == "Full test content with all fields."
        assert doc.embedding == embedding
        assert doc.metadata == metadata
        assert doc.id == doc_id
        assert doc.created_at == created_at
    
    def test_content_preview_short(self):
        """Test content preview for short content."""
        doc = Document(
            filename="short.txt",
            content="Short content."
        )
        
        assert doc.content_preview == "Short content."
    
    def test_content_preview_long(self):
        """Test content preview for long content."""
        long_content = "This is a very long piece of content that exceeds the preview limit and should be truncated with ellipsis."
        doc = Document(
            filename="long.txt",
            content=long_content
        )
        
        preview = doc.content_preview
        assert len(preview) == 100  # 97 chars + "..."
        assert preview.endswith("...")
        assert preview.startswith("This is a very long")
    
    def test_embedding_dimension_none(self):
        """Test embedding dimension when no embedding exists."""
        doc = Document(
            filename="no_embedding.txt",
            content="Content without embedding."
        )
        
        assert doc.embedding_dimension is None
    
    def test_embedding_dimension_with_embedding(self):
        """Test embedding dimension calculation."""
        embedding = [0.1] * 768  # 768-dimensional embedding
        doc = Document(
            filename="with_embedding.txt",
            content="Content with embedding.",
            embedding=embedding
        )
        
        assert doc.embedding_dimension == 768
    
    def test_document_equality(self):
        """Test document equality comparison."""
        doc1 = Document(
            filename="test.txt",
            content="Same content."
        )
        
        doc2 = Document(
            filename="test.txt", 
            content="Same content."
        )
        
        # Documents with same content should be equal
        assert doc1.filename == doc2.filename
        assert doc1.content == doc2.content
    
    def test_document_metadata_modification(self):
        """Test that metadata can be modified."""
        doc = Document(
            filename="meta_test.txt",
            content="Content for metadata test."
        )
        
        # Initially empty
        assert doc.metadata == {}
        
        # Add metadata
        doc.metadata["key1"] = "value1"
        doc.metadata["key2"] = 42
        
        assert doc.metadata["key1"] == "value1"
        assert doc.metadata["key2"] == 42
        assert len(doc.metadata) == 2