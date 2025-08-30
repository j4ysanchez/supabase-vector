"""Tests for the CLI interface."""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from pathlib import Path

from vector_db.cli import cli
from vector_db.models import Document


class TestCLI:
    """Test the CLI interface."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_vector_db(self):
        """Create a mock VectorDB for CLI testing."""
        mock_db = Mock()
        
        # Mock async methods
        mock_db.ingest_file = AsyncMock(return_value="Successfully ingested test.txt (ID: 123)")
        mock_db.ingest_directory = AsyncMock(return_value=["Success: file1.txt", "Success: file2.txt"])
        mock_db.health_check = AsyncMock(return_value={'ollama': True, 'supabase': True, 'overall': True})
        
        # Mock sync methods
        mock_db.search_by_text.return_value = [
            Document(filename="doc1.txt", content="Test content", id=uuid4()),
            Document(filename="doc2.txt", content="Another test", id=uuid4())
        ]
        mock_db.list_documents.return_value = [
            Document(filename="doc1.txt", content="Content 1", id=uuid4()),
            Document(filename="doc2.txt", content="Content 2", id=uuid4())
        ]
        mock_db.get_document.return_value = Document(
            filename="test.txt", 
            content="Test document content", 
            id=uuid4()
        )
        mock_db.delete_document.return_value = True
        mock_db.get_stats.return_value = {
            'total_documents': 5,
            'total_content_size': 1000,
            'average_document_size': 200,
            'file_types': {'.txt': 3, '.md': 2},
            'config': {
                'chunk_size': 1000,
                'supported_extensions': ['.txt', '.md'],
                'max_file_size_mb': 100
            }
        }
        
        return mock_db
    
    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Vector Database CLI" in result.output
        assert "ingest" in result.output
        assert "search" in result.output
        assert "list" in result.output
    
    def test_ingest_command_success(self, runner, mock_vector_db, temp_text_file):
        """Test successful file ingestion command."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['ingest', str(temp_text_file)])
            
            assert result.exit_code == 0
            assert "✅" in result.output
            assert "Successfully ingested" in result.output
            mock_vector_db.ingest_file.assert_called_once()
    
    def test_ingest_command_file_not_found(self, runner):
        """Test ingest command with non-existent file."""
        result = runner.invoke(cli, ['ingest', '/non/existent/file.txt'])
        
        assert result.exit_code != 0
        # Click should handle the file not found error
    
    def test_ingest_command_error(self, runner, mock_vector_db, temp_text_file):
        """Test ingest command with processing error."""
        mock_vector_db.ingest_file.side_effect = Exception("Processing failed")
        
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['ingest', str(temp_text_file)])
            
            assert result.exit_code != 0
            assert "❌ Error:" in result.output
            assert "Processing failed" in result.output
    
    def test_ingest_dir_command_success(self, runner, mock_vector_db, temp_directory):
        """Test successful directory ingestion command."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['ingest-dir', str(temp_directory)])
            
            assert result.exit_code == 0
            assert "📁 Processed" in result.output
            assert "✅ Success:" in result.output
            mock_vector_db.ingest_directory.assert_called_once()
    
    def test_ingest_dir_command_recursive(self, runner, mock_vector_db, temp_directory):
        """Test directory ingestion with recursive flag."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['ingest-dir', str(temp_directory), '--recursive'])
            
            assert result.exit_code == 0
            # Check that recursive=True was passed
            call_args = mock_vector_db.ingest_directory.call_args
            assert call_args[0][1] is True  # recursive parameter
    
    def test_search_command_success(self, runner, mock_vector_db):
        """Test successful search command."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['search', 'test query'])
            
            assert result.exit_code == 0
            assert "🔍 Found" in result.output
            assert "documents matching" in result.output
            assert "doc1.txt" in result.output
            mock_vector_db.search_by_text.assert_called_once_with('test query', 5)
    
    def test_search_command_no_results(self, runner, mock_vector_db):
        """Test search command with no results."""
        mock_vector_db.search_by_text.return_value = []
        
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['search', 'no matches'])
            
            assert result.exit_code == 0
            assert "🔍 No documents found" in result.output
    
    def test_search_command_with_limit(self, runner, mock_vector_db):
        """Test search command with custom limit."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['search', 'test', '--limit', '10'])
            
            assert result.exit_code == 0
            mock_vector_db.search_by_text.assert_called_once_with('test', 10)
    
    def test_list_command_success(self, runner, mock_vector_db):
        """Test successful list command."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['list'])
            
            assert result.exit_code == 0
            assert "📄 Found" in result.output
            assert "documents:" in result.output
            assert "doc1.txt" in result.output
            mock_vector_db.list_documents.assert_called_once_with(20, 0)
    
    def test_list_command_empty(self, runner, mock_vector_db):
        """Test list command with no documents."""
        mock_vector_db.list_documents.return_value = []
        
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['list'])
            
            assert result.exit_code == 0
            assert "📄 No documents found" in result.output
    
    def test_list_command_with_pagination(self, runner, mock_vector_db):
        """Test list command with pagination options."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['list', '--limit', '5', '--offset', '10'])
            
            assert result.exit_code == 0
            mock_vector_db.list_documents.assert_called_once_with(5, 10)
    
    def test_get_command_success(self, runner, mock_vector_db):
        """Test successful get command."""
        doc_id = str(uuid4())
        
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['get', doc_id])
            
            assert result.exit_code == 0
            assert "📄 Document:" in result.output
            assert "test.txt" in result.output
            assert "Content preview:" in result.output
    
    def test_get_command_not_found(self, runner, mock_vector_db):
        """Test get command with non-existent document."""
        doc_id = str(uuid4())
        mock_vector_db.get_document.return_value = None
        
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['get', doc_id])
            
            assert result.exit_code == 0
            assert "❌ Document not found" in result.output
    
    def test_get_command_invalid_uuid(self, runner, mock_vector_db):
        """Test get command with invalid UUID."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['get', 'invalid-uuid'])
            
            assert result.exit_code != 0
            assert "❌ Invalid UUID format" in result.output
    
    def test_delete_command_success(self, runner, mock_vector_db):
        """Test successful delete command."""
        doc_id = str(uuid4())
        
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            # Simulate user confirmation
            result = runner.invoke(cli, ['delete', doc_id], input='y\n')
            
            assert result.exit_code == 0
            assert "✅ Document deleted successfully" in result.output
            mock_vector_db.delete_document.assert_called_once()
    
    def test_delete_command_cancelled(self, runner, mock_vector_db):
        """Test delete command when user cancels."""
        doc_id = str(uuid4())
        
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            # Simulate user cancellation
            result = runner.invoke(cli, ['delete', doc_id], input='n\n')
            
            assert result.exit_code != 0
            # Should not call delete if cancelled
            mock_vector_db.delete_document.assert_not_called()
    
    def test_health_command_all_healthy(self, runner, mock_vector_db):
        """Test health command when all services are healthy."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['health'])
            
            assert result.exit_code == 0
            assert "🏥 Health Check Results:" in result.output
            assert "✅ Ollama: Healthy" in result.output
            assert "✅ Supabase: Healthy" in result.output
            assert "✅ Overall: All systems operational" in result.output
    
    def test_health_command_partial_failure(self, runner, mock_vector_db):
        """Test health command when some services are down."""
        mock_vector_db.health_check.return_value = {
            'ollama': True, 
            'supabase': False, 
            'overall': False
        }
        
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['health'])
            
            assert result.exit_code != 0
            assert "✅ Ollama: Healthy" in result.output
            assert "❌ Supabase: Unhealthy" in result.output
            assert "❌ Overall: Some systems down" in result.output
    
    def test_stats_command_success(self, runner, mock_vector_db):
        """Test successful stats command."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['stats'])
            
            assert result.exit_code == 0
            assert "📊 Database Statistics:" in result.output
            assert "📄 Total documents: 5" in result.output
            assert "💾 Total content size: 1,000 bytes" in result.output
            assert "📁 File types:" in result.output
            assert "⚙️  Configuration:" in result.output
    
    def test_stats_command_error(self, runner, mock_vector_db):
        """Test stats command with error."""
        mock_vector_db.get_stats.return_value = {'error': 'Database connection failed'}
        
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['stats'])
            
            assert result.exit_code == 0
            assert "❌ Error getting stats:" in result.output
            assert "Database connection failed" in result.output
    
    def test_config_command_success(self, runner):
        """Test successful config command."""
        with patch('vector_db.config.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.print_summary = Mock()
            mock_get_config.return_value = mock_config
            
            result = runner.invoke(cli, ['config'])
            
            assert result.exit_code == 0
            mock_config.print_summary.assert_called_once()
    
    def test_verbose_flag(self, runner, mock_vector_db, temp_text_file):
        """Test CLI with verbose flag."""
        with patch('vector_db.cli.VectorDB', return_value=mock_vector_db):
            result = runner.invoke(cli, ['--verbose', 'ingest', str(temp_text_file)])
            
            assert result.exit_code == 0
            # Verbose flag should enable logging, but we can't easily test the logging output