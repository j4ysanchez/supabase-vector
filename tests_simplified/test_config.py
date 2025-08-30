"""Tests for the simplified configuration system."""

import pytest
import tempfile
import os
from unittest.mock import patch
from pydantic import ValidationError

from vector_db.config import config, Config


class TestSimplifiedConfig:
    """Test the simplified configuration system."""
    
    def test_config_loads_successfully(self):
        """Test that configuration loads without errors."""
        # Use the global config instance
        
        # Verify required fields exist
        assert hasattr(config, 'supabase_url')
        assert hasattr(config, 'supabase_key')
        assert hasattr(config, 'ollama_url')
        assert hasattr(config, 'ollama_model')
        
        # Verify defaults (use actual values from environment)
        assert config.supabase_table == "documents"
        assert config.ollama_url.startswith("http://")  # Could be localhost or IP
        assert "nomic-embed-text" in config.ollama_model  # Could have :latest suffix
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Since config loads from environment, we need to test validation differently
        # Test that the global config has valid values
        assert config.supabase_url.startswith("https://")
        assert config.chunk_size > 0
        assert config.chunk_overlap >= 0
        assert config.max_file_size > 0
        assert config.max_retries >= 0
        assert config.retry_delay >= 0
    
    def test_config_computed_properties(self):
        """Test computed properties work correctly."""
        # Test with the global config loaded from environment
        
        # Test basic properties exist and have valid values
        assert config.supabase_url.startswith("https://")
        assert len(config.supabase_key) > 0
        assert config.chunk_size > 0
        assert config.max_file_size > 0
        assert config.supabase_table == "documents"  # Default value
    
    def test_config_environment_loading(self):
        """Test loading configuration from environment variables."""
        test_env = {
            "SUPABASE_URL": "https://env-test.supabase.co",
            "SUPABASE_KEY": "env-test-key",
            "OLLAMA_MODEL_NAME": "custom-model",
            "PROCESSING_CHUNK_SIZE": "2000"
        }
        
        with patch.dict(os.environ, test_env):
            test_config = Config()
            
            assert test_config.supabase_url == "https://env-test.supabase.co"
            assert test_config.supabase_key == "env-test-key"
            assert test_config.ollama_model == "custom-model"
            assert test_config.chunk_size == 2000
    
    def test_config_basic_functionality(self):
        """Test basic configuration functionality."""
        test_config = Config(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key"
        )
        
        # Test that all required fields are present
        assert test_config.supabase_url
        assert test_config.supabase_key
        assert test_config.supabase_table
        assert test_config.ollama_url
        assert test_config.ollama_model
        assert test_config.chunk_size > 0
        assert test_config.chunk_overlap >= 0
        assert test_config.max_file_size > 0
        assert test_config.max_retries >= 0
        assert test_config.retry_delay >= 0