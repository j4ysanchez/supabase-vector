#!/usr/bin/env python3
"""Display current configuration loaded from .env file."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.config import ApplicationConfig, ConfigValidationError


def main():
    """Display the current configuration."""
    print("Current Project Configuration")
    print("=" * 35)
    
    try:
        config = ApplicationConfig.from_env()
        
        print("\n🔗 Supabase Configuration:")
        print(f"  URL: {config.supabase.url}")
        print(f"  Table: {config.supabase.table_name}")
        print(f"  Timeout: {config.supabase.timeout}s")
        print(f"  Max Retries: {config.supabase.max_retries}")
        print(f"  Service Key: {config.supabase.service_key[:20]}... ({len(config.supabase.service_key)} chars)")
        
        print("\n🤖 Ollama Configuration:")
        print(f"  Base URL: {config.ollama.base_url}")
        print(f"  Model: {config.ollama.model_name}")
        print(f"  Timeout: {config.ollama.timeout}s")
        print(f"  Max Retries: {config.ollama.max_retries}")
        print(f"  Batch Size: {config.ollama.batch_size}")
        
        print("\n📄 Processing Configuration:")
        print(f"  Chunk Size: {config.processing.chunk_size} characters")
        print(f"  Chunk Overlap: {config.processing.chunk_overlap} characters")
        print(f"  Max File Size: {config.processing.max_file_size_mb}MB ({config.processing.max_file_size_bytes:,} bytes)")
        print(f"  Supported Extensions: {', '.join(config.processing.supported_extensions)}")
        
        print("\n📝 Logging Configuration:")
        print(f"  Level: {config.logging.level}")
        print(f"  Format: {config.logging.format}")
        print(f"  Date Format: {config.logging.date_format}")
        print(f"  Log File: {config.logging.log_file or 'Console only'}")
        
        print("\n✅ Configuration loaded successfully!")
        
        return 0
        
    except ConfigValidationError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nConfiguration Help:")
        print("-" * 20)
        
        # Try to create a minimal config to show help
        try:
            import os
            os.environ["SUPABASE_URL"] = "https://example.supabase.co"
            os.environ["SUPABASE_KEY"] = "example-key"
            os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
            
            temp_config = ApplicationConfig.from_env(env_file=None)
            print(temp_config.print_config_help())
        except:
            print("Please check your .env file and ensure required variables are set.")
        
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())