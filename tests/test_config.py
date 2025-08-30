"""
Test configuration management.
"""
import pytest
import os
from unittest.mock import patch
from src.config import Config


@pytest.mark.unit
def test_config_creation():
    """Test basic configuration creation."""
    config = Config(
        supabase_url="https://test.supabase.co",
        supabase_anon_key="test-anon-key",
        supabase_service_key="test-service-key"
    )
    
    # Test that config has required attributes
    assert hasattr(config, 'supabase_url')
    assert hasattr(config, 'supabase_anon_key')
    assert hasattr(config, 'supabase_service_key')
    assert hasattr(config, 'supabase_table')
    assert hasattr(config, 'ollama_url')
    assert hasattr(config, 'ollama_model')
    assert hasattr(config, 'chunk_size')
    assert hasattr(config, 'chunk_overlap')


@pytest.mark.unit
def test_config_validation():
    """Test configuration validation."""
    # Missing required fields should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        Config(supabase_url="", supabase_anon_key="", supabase_service_key="")


@pytest.mark.unit
def test_config_url_validation():
    """Test URL validation."""
    # Invalid URL should raise validation error
    with pytest.raises(Exception):
        Config(
            supabase_url="not-a-url",
            supabase_anon_key="test-key",
            supabase_service_key="test-key"
        )


@pytest.mark.unit
def test_config_properties():
    """Test configuration properties."""
    config = Config(
        supabase_url="https://test.supabase.co",
        supabase_anon_key="test-key",
        supabase_service_key="test-key"
    )
    
    # Test computed properties work
    assert config.max_file_size_bytes > 0
    assert isinstance(config.extensions_list, tuple)
    assert len(config.extensions_list) > 0


@pytest.mark.unit
def test_config_has_required_fields():
    """Test that config has all required fields."""
    config = Config(
        supabase_url="https://test.supabase.co",
        supabase_anon_key="test-key",
        supabase_service_key="test-key"
    )
    
    # Test all required fields are present
    assert config.supabase_url
    assert config.supabase_anon_key
    assert config.supabase_service_key
    assert config.supabase_table
    assert config.ollama_url
    assert config.ollama_model
    assert config.chunk_size > 0
    assert config.chunk_overlap >= 0