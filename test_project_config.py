#!/usr/bin/env python3
"""Test script to validate the project's specific configuration values."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.config import ApplicationConfig, ConfigValidationError


def test_project_specific_values():
    """Test that the project's .env file contains expected values."""
    print("Testing project-specific configuration values...")
    
    try:
        config = ApplicationConfig.from_env(Path(".env"))
        
        # Test Supabase configuration
        expected_supabase_url = "https://tmbotmpvcrbbqvezzrui.supabase.co"
        assert config.supabase.url == expected_supabase_url, f"Expected {expected_supabase_url}, got {config.supabase.url}"
        assert config.supabase.table_name == "documents"
        assert config.supabase.timeout == 30
        assert config.supabase.max_retries == 3
        print("✅ Supabase configuration matches expected values")
        
        # Test Ollama configuration
        expected_ollama_url = "http://10.0.0.245:11434"
        assert config.ollama.base_url == expected_ollama_url, f"Expected {expected_ollama_url}, got {config.ollama.base_url}"
        assert config.ollama.model_name == "nomic-embed-text"
        assert config.ollama.timeout == 60
        assert config.ollama.max_retries == 3
        assert config.ollama.batch_size == 32
        print("✅ Ollama configuration matches expected values")
        
        # Test Processing configuration
        assert config.processing.chunk_size == 1000
        assert config.processing.chunk_overlap == 200
        assert config.processing.max_file_size_mb == 100
        assert config.processing.supported_extensions == (".txt",)
        print("✅ Processing configuration matches expected values")
        
        # Test Logging configuration
        assert config.logging.level == "INFO"
        assert "%(asctime)s - %(name)s - %(levelname)s - %(message)s" in config.logging.format
        assert config.logging.date_format == "%Y-%m-%d %H:%M:%S"
        assert config.logging.log_file is None  # Should be None since LOG_FILE is commented out
        print("✅ Logging configuration matches expected values")
        
        return True
        
    except AssertionError as e:
        print(f"❌ Configuration value mismatch: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to validate project configuration: {e}")
        return False


def test_service_key_validation():
    """Test that the service key is properly loaded and validated."""
    print("\nTesting service key validation...")
    
    try:
        config = ApplicationConfig.from_env(Path(".env"))
        
        # Verify service key is loaded
        assert config.supabase.service_key is not None
        assert len(config.supabase.service_key) > 0
        
        # Verify it looks like a JWT token (starts with eyJ)
        assert config.supabase.service_key.startswith("eyJ"), "Service key should be a JWT token"
        
        # Verify it has the expected structure (3 parts separated by dots)
        parts = config.supabase.service_key.split(".")
        assert len(parts) == 3, "JWT should have 3 parts separated by dots"
        
        print("✅ Service key is properly loaded and appears to be a valid JWT")
        print(f"  - Key starts with: {config.supabase.service_key[:20]}...")
        print(f"  - Key length: {len(config.supabase.service_key)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Service key validation failed: {e}")
        return False


def test_url_validation():
    """Test that URLs are properly validated."""
    print("\nTesting URL validation...")
    
    try:
        config = ApplicationConfig.from_env(Path(".env"))
        
        # Test Supabase URL
        assert config.supabase.url.startswith("https://"), "Supabase URL should use HTTPS"
        assert ".supabase.co" in config.supabase.url, "Should be a Supabase URL"
        
        # Test Ollama URL
        assert config.ollama.base_url.startswith("http://"), "Ollama URL should use HTTP (local)"
        assert ":11434" in config.ollama.base_url, "Should use Ollama's default port"
        
        print("✅ All URLs are properly formatted")
        print(f"  - Supabase URL: {config.supabase.url}")
        print(f"  - Ollama URL: {config.ollama.base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ URL validation failed: {e}")
        return False


def test_processing_limits():
    """Test processing configuration limits and calculations."""
    print("\nTesting processing limits and calculations...")
    
    try:
        config = ApplicationConfig.from_env(Path(".env"))
        
        # Test chunk size and overlap relationship
        assert config.processing.chunk_overlap < config.processing.chunk_size, \
            "Chunk overlap should be less than chunk size"
        
        # Test max file size calculation
        expected_bytes = 100 * 1024 * 1024  # 100MB in bytes
        assert config.processing.max_file_size_bytes == expected_bytes, \
            f"Expected {expected_bytes} bytes, got {config.processing.max_file_size_bytes}"
        
        # Test supported extensions
        assert ".txt" in config.processing.supported_extensions, \
            "Should support .txt files"
        
        print("✅ Processing limits are properly configured")
        print(f"  - Chunk size: {config.processing.chunk_size} characters")
        print(f"  - Chunk overlap: {config.processing.chunk_overlap} characters")
        print(f"  - Max file size: {config.processing.max_file_size_mb}MB ({config.processing.max_file_size_bytes:,} bytes)")
        print(f"  - Supported extensions: {config.processing.supported_extensions}")
        
        return True
        
    except Exception as e:
        print(f"❌ Processing limits test failed: {e}")
        return False


def test_logging_setup():
    """Test that logging can be properly configured."""
    print("\nTesting logging setup...")
    
    try:
        config = ApplicationConfig.from_env(Path(".env"))
        
        # Test logging configuration
        config.setup_logging()
        
        # Test log level conversion
        import logging
        expected_level = logging.INFO
        assert config.logging.get_log_level() == expected_level, \
            f"Expected log level {expected_level}, got {config.logging.get_log_level()}"
        
        print("✅ Logging setup completed successfully")
        print(f"  - Log level: {config.logging.level} ({config.logging.get_log_level()})")
        print(f"  - Log format: {config.logging.format}")
        print(f"  - Date format: {config.logging.date_format}")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging setup test failed: {e}")
        return False


def main():
    """Run all project-specific configuration tests."""
    print("Project Configuration Validation Tests")
    print("=" * 45)
    
    tests = [
        test_project_specific_values,
        test_service_key_validation,
        test_url_validation,
        test_processing_limits,
        test_logging_setup
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nTest Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All project configuration tests passed!")
        print("The configuration system is properly set up for this project.")
        return 0
    else:
        print("❌ Some project configuration tests failed.")
        print("Please check the .env file and configuration implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())