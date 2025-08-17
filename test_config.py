#!/usr/bin/env python3
"""Test script to verify configuration management system using project's .env file."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.config import ApplicationConfig, ConfigValidationError


def test_project_env_file():
    """Test configuration loading from the project's .env file."""
    print("Testing configuration loading from project's .env file...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Project .env file not found")
        return False
    
    try:
        # Load configuration from project's .env file
        config = ApplicationConfig.from_env(env_file)
        print("✅ Configuration loaded successfully from .env file")
        
        # Verify required values are present
        assert config.supabase.url, "Supabase URL should not be empty"
        assert config.supabase.service_key, "Supabase service key should not be empty"
        assert config.ollama.base_url, "Ollama base URL should not be empty"
        
        print("✅ All required configuration values are present")
        print(f"  - Supabase URL: {config.supabase.url}")
        print(f"  - Supabase Table: {config.supabase.table_name}")
        print(f"  - Ollama URL: {config.ollama.base_url}")
        print(f"  - Ollama Model: {config.ollama.model_name}")
        print(f"  - Processing Chunk Size: {config.processing.chunk_size}")
        print(f"  - Log Level: {config.logging.level}")
        
        return True
        
    except ConfigValidationError as e:
        print(f"❌ Configuration validation error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error loading configuration: {e}")
        return False


def test_config_validation():
    """Test configuration validation with missing required variables."""
    print("\nTesting configuration validation with missing variables...")
    
    # Create a temporary empty .env file to test with
    empty_env_file = Path("empty.env")
    empty_env_file.write_text("# Empty .env file for testing\n")
    
    # Clear environment variables that might be loaded from system
    env_vars_to_clear = [
        "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_KEY", "OLLAMA_BASE_URL"
    ]
    
    original_values = {}
    for var in env_vars_to_clear:
        original_values[var] = os.getenv(var)
        if var in os.environ:
            del os.environ[var]
    
    try:
        # This should fail due to missing required variables
        config = ApplicationConfig.from_env(env_file=empty_env_file)
        print("❌ Expected ConfigValidationError but configuration loaded successfully")
        return False
    except ConfigValidationError as e:
        print(f"✅ Correctly caught configuration error: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Restore original values
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value
        
        # Clean up temporary file
        if empty_env_file.exists():
            empty_env_file.unlink()


def test_individual_configs():
    """Test individual configuration components with project values."""
    print("\nTesting individual configuration components...")
    
    try:
        # Load from project .env file
        config = ApplicationConfig.from_env(Path(".env"))
        
        # Test Supabase config
        config.supabase.validate()
        print("✅ Supabase configuration is valid")
        
        # Test Ollama config  
        config.ollama.validate()
        print("✅ Ollama configuration is valid")
        
        # Test Processing config
        config.processing.validate()
        print("✅ Processing configuration is valid")
        
        # Test Logging config
        config.logging.validate()
        print("✅ Logging configuration is valid")
        
        # Test logging setup
        config.setup_logging()
        print("✅ Logging setup completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Individual config test failed: {e}")
        return False


def test_config_help():
    """Test configuration help generation."""
    print("\nTesting configuration help generation...")
    
    try:
        config = ApplicationConfig.from_env(Path(".env"))
        help_text = config.print_config_help()
        
        # Verify help text contains expected sections
        assert "Required Environment Variables:" in help_text
        assert "SUPABASE_URL" in help_text
        assert "OLLAMA_BASE_URL" in help_text
        assert "Example .env file:" in help_text
        
        print("✅ Configuration help generated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate configuration help: {e}")
        return False


def main():
    """Run all configuration tests."""
    print("Configuration Management System Test (Using Project .env)")
    print("=" * 60)
    
    tests = [
        test_project_env_file,
        test_config_validation,
        test_individual_configs,
        test_config_help
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nTest Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Configuration system works with project .env file.")
        return 0
    else:
        print("❌ Some tests failed. Please check the configuration or implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())