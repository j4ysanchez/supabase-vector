"""Tests for the simplified configuration system."""

import pytest
import tempfile
import os
from unittest.mock import patch
from pydantic import ValidationError

from vector_db.config import get_config, Config


class TestSimplifiedConfig:
    """Test the simplified configuration system."""
    
    def test_config_loads_successfully(self):
        """Test that configuration loads without errors."""
        config = get_config()
        
        # Verify required fields exist
        assert hasattr(config, 'supabase_url')
        assert hasattr(config, 'supabase_anon_key')
        assert hasattr(config, 'ollama_url')
        assert hasattr(config, 'ollama_model')
        
        # Verify defaults (use actual values from environment)
        assert config.supabase_table == "documents"
        assert config.ollama_url.startswith("http://")  # Could be localhost or IP
        assert "nomic-embed-text" in config.ollama_model  # Could have :latest suffix
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid URL format
        with pytest.raises(ValidationError):
            Config(
                supabase_url="invalid-url",
                supabase_key="test-key"
            )
        
        # Test invalid numeric values
        with pytest.raises(ValidationError):
            Config(
                supabase_url="https://test.supabase.co",
                supabase_key="test-key",
                ollama_timeout=-1  # Invalid negative timeout
            )
    
    def test_config_computed_properties(self):
        """Test computed properties work correctly."""
        # Test with the actual config values from environment
        config = Config(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key"
        )
        
        # Test computed properties - use the actual values from config
        expected_bytes = config.max_file_size_mb * 1024 * 1024
        assert config.max_file_size_bytes == expected_bytes
        assert isinstance(config.extensions_list, tuple)
        assert ".txt" in config.extensions_list
    
    def test_config_environment_loading(self):
        """Test loading configuration from environment variables."""
        test_env = {
            "SUPABASE_URL": "https://env-test.supabase.co",
            "SUPABASE_KEY": "env-test-key",
            "OLLAMA_MODEL_NAME": "custom-model",
            "PROCESSING_CHUNK_SIZE": "2000"
        }
        
        with patch.dict(os.environ, test_env):
            config = Config()
            
            assert config.supabase_url == "https://env-test.supabase.co"
            assert config.supabase_anon_key == "env-test-key"
            assert config.ollama_model == "custom-model"
            assert config.chunk_size == 2000
    
    def test_config_summary_output(self, capsys):
        """Test configuration summary output."""
        config = Config(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key"
        )
        
        config.print_summary()
        captured = capsys.readouterr()
        
        assert "Configuration Summary" in captured.out
        assert "Supabase:" in captured.out
        assert "Ollama:" in captured.out
        assert "Processing:" in captured.out
        assert "Logging:" in captured.out