"""
Test CLI functionality.
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from pathlib import Path

from vector_db.cli import cli, ingest, search, health


@pytest.fixture
def cli_runner():
    """Click CLI test runner."""
    return CliRunner()


@pytest.mark.unit
def test_cli_help(cli_runner):
    """Test CLI help command."""
    result = cli_runner.invoke(cli, ['--help'])
    
    assert result.exit_code == 0
    assert 'Vector Database CLI' in result.output
    assert 'ingest' in result.output
    assert 'search' in result.output
    assert 'health' in result.output


@pytest.mark.unit
def test_ingest_command_help(cli_runner):
    """Test ingest command help."""
    result = cli_runner.invoke(ingest, ['--help'])
    
    assert result.exit_code == 0
    assert 'Ingest documents' in result.output


@pytest.mark.unit
def test_search_command_help(cli_runner):
    """Test search command help."""
    result = cli_runner.invoke(search, ['--help'])
    
    assert result.exit_code == 0
    assert 'Search documents' in result.output


@pytest.mark.unit
def test_health_command_help(cli_runner):
    """Test health command help."""
    result = cli_runner.invoke(health, ['--help'])
    
    assert result.exit_code == 0
    assert 'Check the health' in result.output


@pytest.mark.unit
def test_ingest_missing_file(cli_runner):
    """Test ingest with non-existent file."""
    result = cli_runner.invoke(ingest, ['nonexistent.txt'])
    
    assert result.exit_code != 0
    assert 'does not exist' in result.output


@pytest.mark.unit
@patch('vector_db.cli.VectorDB')
@patch('vector_db.cli.asyncio.run')
def test_ingest_success(mock_asyncio_run, mock_vector_db, cli_runner, temp_file):
    """Test successful document ingestion."""
    # Mock VectorDB
    mock_db = Mock()
    mock_vector_db.return_value = mock_db
    mock_asyncio_run.return_value = "Successfully ingested test.txt (ID: 123)"
    
    result = cli_runner.invoke(ingest, [str(temp_file)])
    
    assert result.exit_code == 0
    assert 'Successfully ingested' in result.output
    mock_asyncio_run.assert_called_once()


@pytest.mark.unit
@patch('vector_db.cli.VectorDB')
def test_search_success(mock_vector_db, cli_runner):
    """Test successful document search."""
    from vector_db.models import Document
    
    # Mock VectorDB
    mock_db = Mock()
    mock_vector_db.return_value = mock_db
    mock_doc = Document(filename="test.txt", content="Test content for preview")
    mock_db.search_by_text.return_value = [mock_doc]
    
    result = cli_runner.invoke(search, ['test query'])
    
    assert result.exit_code == 0
    assert 'test.txt' in result.output
    assert 'Test content' in result.output
    mock_db.search_by_text.assert_called_once_with('test query', limit=5)


@pytest.mark.unit
@patch('vector_db.cli.VectorDB')
def test_search_no_results(mock_vector_db, cli_runner):
    """Test search with no results."""
    # Mock VectorDB
    mock_db = Mock()
    mock_vector_db.return_value = mock_db
    mock_db.search_by_text.return_value = []
    
    result = cli_runner.invoke(search, ['nonexistent query'])
    
    assert result.exit_code == 0
    assert 'No documents found' in result.output


@pytest.mark.unit
@patch('vector_db.cli.VectorDB')
@patch('vector_db.cli.asyncio.run')
def test_health_success(mock_asyncio_run, mock_vector_db, cli_runner):
    """Test health command success."""
    # Mock VectorDB
    mock_db = Mock()
    mock_vector_db.return_value = mock_db
    mock_asyncio_run.return_value = {
        'ollama': True,
        'supabase': True,
        'overall': True
    }
    
    result = cli_runner.invoke(health)
    
    assert result.exit_code == 0
    assert 'Ollama: Healthy' in result.output
    assert 'Supabase: Healthy' in result.output
    assert 'Overall: All systems operational' in result.output


@pytest.mark.unit
@patch('vector_db.cli.VectorDB')
@patch('vector_db.cli.asyncio.run')
def test_ingest_with_error(mock_asyncio_run, mock_vector_db, cli_runner, temp_file):
    """Test ingest command with processing error."""
    # Mock VectorDB with error
    mock_db = Mock()
    mock_vector_db.return_value = mock_db
    mock_asyncio_run.side_effect = Exception("Processing failed")
    
    result = cli_runner.invoke(ingest, [str(temp_file)])
    
    assert result.exit_code != 0
    assert 'Error' in result.output


@pytest.mark.unit
def test_search_with_limit(cli_runner):
    """Test search command with custom limit."""
    with patch('vector_db.cli.VectorDB') as mock_vector_db:
        mock_db = Mock()
        mock_vector_db.return_value = mock_db
        mock_db.search_by_text.return_value = []
        
        result = cli_runner.invoke(search, ['test query', '--limit', '3'])
        
        assert result.exit_code == 0
        mock_db.search_by_text.assert_called_once_with('test query', limit=3)


@pytest.mark.integration
def test_cli_integration(cli_runner, temp_file):
    """Integration test with real components (requires services)."""
    # This would test the full CLI with real services
    # Skip if services not available
    pytest.skip("Integration test - requires running services")