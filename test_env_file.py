#!/usr/bin/env python3
"""Test script to verify .env file loading and environment variable precedence."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.config import ApplicationConfig, ConfigValidationError


def test_project_env_loading():
    """Test loading configuration from the project's .env file."""
    print("Testing project .env file loading...")
    
    try:
        # Load configuration from project's .env file
        config = ApplicationConfig.from_env(Path(".env"))
        
        print("✅ Configuration loaded from project .env file")
        
        # Display actual values from project .env
        print(f"  - Supabase URL: {config.supabase.url}")
        print(f"  - Supabase Table: {config.supabase.table_name}")
        print(f"  - Ollama URL: {config.ollama.base_url}")
        print(f"  - Ollama Model: {config.ollama.model_name}")
        print(f"  - Chunk Size: {config.processing.chunk_size}")
        print(f"  - Chunk Overlap: {config.processing.chunk_overlap}")
        print(f"  - Max File Size: {config.processing.max_file_size_mb}MB")
        print(f"  - Supported Extensions: {config.processing.supported_extensions}")
        print(f"  - Log Level: {config.logging.level}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load configuration from project .env file: {e}")
        return False


def test_env_var_precedence():
    """Test that environment variables take precedence over .env file."""
    print("\nTesting environment variable precedence...")
    
    try:
        # Set an environment variable that should override .env file
        original_log_level = os.getenv("LOG_LEVEL")
        os.environ["LOG_LEVEL"] = "DEBUG"
        
        config = ApplicationConfig.from_env(Path(".env"))
        
        # Should use the environment variable value, not .env file value
        assert config.logging.level == "DEBUG"
        print("✅ Environment variable correctly overrides .env file value")
        print(f"  - Log Level from env var: {config.logging.level}")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment variable precedence test failed: {e}")
        return False
    finally:
        # Restore original value
        if original_log_level is not None:
            os.environ["LOG_LEVEL"] = original_log_level
        elif "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]


def test_backward_compatibility():
    """Test backward compatibility with SUPABASE_KEY vs SUPABASE_SERVICE_KEY."""
    print("\nTesting backward compatibility for Supabase key naming...")
    
    try:
        # Load config normally (should work with SUPABASE_KEY from .env)
        config = ApplicationConfig.from_env(Path(".env"))
        
        # Verify the service key was loaded (from SUPABASE_KEY in .env)
        assert config.supabase.service_key is not None
        assert len(config.supabase.service_key) > 0
        
        print("✅ Backward compatibility works - SUPABASE_KEY loaded successfully")
        print(f"  - Service key loaded: {config.supabase.service_key[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False


def test_missing_env_file():
    """Test behavior when .env file doesn't exist."""
    print("\nTesting behavior with missing .env file...")
    
    try:
        # Try to load from non-existent file
        config = ApplicationConfig.from_env(Path("nonexistent.env"))
        print("❌ Expected error for missing .env file but loaded successfully")
        return False
        
    except ConfigValidationError as e:
        if "not found" in str(e):
            print("✅ Correctly caught error for missing .env file")
            return True
        else:
            print(f"❌ Wrong error type for missing file: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error for missing file: {e}")
        return False


def test_default_env_loading():
    """Test loading from default .env file (no path specified)."""
    print("\nTesting default .env file loading...")
    
    try:
        # Load without specifying path (should find .env in current directory)
        config = ApplicationConfig.from_env()
        
        print("✅ Configuration loaded from default .env file")
        print(f"  - Supabase URL: {config.supabase.url}")
        print(f"  - Ollama Model: {config.ollama.model_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load from default .env file: {e}")
        return False


def main():
    """Run all .env file loading tests."""
    print("Environment File Loading Tests")
    print("=" * 40)
    
    tests = [
        test_project_env_loading,
        test_env_var_precedence,
        test_backward_compatibility,
        test_missing_env_file,
        test_default_env_loading
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nTest Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All .env file tests passed!")
        return 0
    else:
        print("❌ Some .env file tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())