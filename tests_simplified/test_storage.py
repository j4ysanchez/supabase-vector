"""Tests for the simplified storage client."""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4, UUID
from datetime import datetime

from vector_db.storage import StorageClient
from vector_db.models import Document


class TestStorageClient:
    """Test the simplified storage client."""
    
    @pytest.fixture
    def storage_client(self):
        """Create a storage client for testing."""
        return StorageClient()
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create a mock Supabase client."""
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        
        # Mock successful operations
        mock_result = Mock()
        mock_result.data = [{"id": str(uuid4()), "filename": "test.txt"}]
        mock_table.insert.return_value.execute.return_value = mock_result
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_result
        mock_table.select.return_value.range.return_value.order.return_value.execute.return_value = mock_result
        mock_table.delete.return_value.eq.return_value.execute.return_value = mock_result
        mock_table.select.return_value.ilike.return_value.limit.return_value.execute.return_value = mock_result
        mock_table.select.return_value.limit.return_value.execute.return_value = mock_result
        
        return mock_client
    
    def test_storage_client_initialization(self, storage_client):
        """Test storage client initialization."""
        assert storage_client.url is not None
        assert storage_client.key is not None
        assert storage_client.table is not None
        assert storage_client.timeout > 0
        assert storage_client.max_retries >= 0
        assert storage_client._client is None
    
    def test_get_client_success(self, storage_client, mock_supabase_client):
        """Test successful client creation."""
        with patch('supabase.create_client', return_value=mock_supabase_client):
            client = storage_client._get_client()
            
            assert client == mock_supabase_client
            assert storage_client._client == mock_supabase_client
    
    def test_get_client_import_error(self, storage_client):
        """Test client creation with missing supabase package."""
        with patch('supabase.create_client', side_effect=ImportError("No module named 'supabase'")):
            with pytest.raises(ImportError, match="Supabase client not installed"):
                storage_client._get_client()
    
    def test_store_document_success(self, storage_client, mock_supabase_client, sample_document):
        """Test successful document storage."""
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            doc_id = storage_client.store_document(sample_document)
            
            assert isinstance(doc_id, UUID)
            mock_supabase_client.table.assert_called_once_with(storage_client.table)
            mock_supabase_client.table().insert.assert_called_once()
    
    def test_store_document_with_existing_id(self, storage_client, mock_supabase_client, sample_document):
        """Test storing document with existing ID."""
        existing_id = uuid4()
        sample_document.id = existing_id
        
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            doc_id = storage_client.store_document(sample_document)
            
            assert doc_id == existing_id
    
    def test_store_document_failure(self, storage_client, mock_supabase_client, sample_document):
        """Test document storage failure."""
        mock_supabase_client.table().insert().execute.side_effect = Exception("Storage error")
        
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            with pytest.raises(Exception, match="Storage failed"):
                storage_client.store_document(sample_document)
    
    def test_get_document_success(self, storage_client, mock_supabase_client):
        """Test successful document retrieval."""
        doc_id = uuid4()
        mock_data = {
            "id": str(doc_id),
            "filename": "test.txt",
            "content": "test content",
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {"test": True},
            "created_at": "2023-01-01T00:00:00+00:00"
        }
        mock_result = Mock()
        mock_result.data = [mock_data]
        mock_supabase_client.table().select().eq().execute.return_value = mock_result
        
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            doc = storage_client.get_document(doc_id)
            
            assert doc is not None
            assert doc.id == doc_id
            assert doc.filename == "test.txt"
            assert doc.content == "test content"
            assert doc.embedding == [0.1, 0.2, 0.3]
            assert doc.metadata == {"test": True}
    
    def test_get_document_not_found(self, storage_client, mock_supabase_client):
        """Test document retrieval when document doesn't exist."""
        doc_id = uuid4()
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_client.table().select().eq().execute.return_value = mock_result
        
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            doc = storage_client.get_document(doc_id)
            
            assert doc is None
    
    def test_list_documents_success(self, storage_client, mock_supabase_client):
        """Test successful document listing."""
        mock_data = [
            {
                "id": str(uuid4()),
                "filename": "doc1.txt",
                "content": "content 1",
                "embedding": None,
                "metadata": {},
                "created_at": "2023-01-01T00:00:00+00:00"
            },
            {
                "id": str(uuid4()),
                "filename": "doc2.txt", 
                "content": "content 2",
                "embedding": [0.1, 0.2],
                "metadata": {"type": "test"},
                "created_at": "2023-01-02T00:00:00+00:00"
            }
        ]
        mock_result = Mock()
        mock_result.data = mock_data
        mock_supabase_client.table().select().range().order().execute.return_value = mock_result
        
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            docs = storage_client.list_documents(limit=10, offset=0)
            
            assert len(docs) == 2
            assert docs[0].filename == "doc1.txt"
            assert docs[1].filename == "doc2.txt"
            assert docs[1].embedding == [0.1, 0.2]
    
    def test_delete_document_success(self, storage_client, mock_supabase_client):
        """Test successful document deletion."""
        doc_id = uuid4()
        mock_result = Mock()
        mock_result.data = [{"id": str(doc_id)}]  # Non-empty data indicates success
        
        # Create a proper mock chain
        mock_execute = Mock(return_value=mock_result)
        mock_eq = Mock(return_value=Mock(execute=mock_execute))
        mock_delete = Mock(return_value=Mock(eq=mock_eq))
        mock_table = Mock(return_value=Mock(delete=mock_delete))
        mock_supabase_client.table = mock_table
        
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            success = storage_client.delete_document(doc_id)
            
            assert success is True
            mock_eq.assert_called_once_with("id", str(doc_id))
    
    def test_delete_document_not_found(self, storage_client, mock_supabase_client):
        """Test document deletion when document doesn't exist."""
        doc_id = uuid4()
        mock_result = Mock()
        mock_result.data = []  # Empty data indicates document not found
        mock_supabase_client.table().delete().eq().execute.return_value = mock_result
        
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            success = storage_client.delete_document(doc_id)
            
            assert success is False
    
    def test_search_by_content_success(self, storage_client, mock_supabase_client):
        """Test successful content search."""
        mock_data = [
            {
                "id": str(uuid4()),
                "filename": "matching_doc.txt",
                "content": "This document contains the search query.",
                "embedding": None,
                "metadata": {},
                "created_at": "2023-01-01T00:00:00+00:00"
            }
        ]
        mock_result = Mock()
        mock_result.data = mock_data
        mock_supabase_client.table().select().ilike().limit().execute.return_value = mock_result
        
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            docs = storage_client.search_by_content("search query", limit=5)
            
            assert len(docs) == 1
            assert docs[0].filename == "matching_doc.txt"
            assert "search query" in docs[0].content
    
    def test_health_check_success(self, storage_client, mock_supabase_client):
        """Test successful health check."""
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_client.table().select().limit().execute.return_value = mock_result
        
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            is_healthy = storage_client.health_check()
            
            assert is_healthy is True
    
    def test_health_check_failure(self, storage_client, mock_supabase_client):
        """Test health check failure."""
        mock_supabase_client.table().select().limit().execute.side_effect = Exception("Connection failed")
        
        with patch.object(storage_client, '_get_client', return_value=mock_supabase_client):
            is_healthy = storage_client.health_check()
            
            assert is_healthy is False