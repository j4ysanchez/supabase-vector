#!/usr/bin/env python3
"""
Migration script to help transition from old configuration system to new simplified one.
This script will check your current .env file and suggest any needed changes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    """Check current configuration and suggest improvements."""
    print("Configuration Migration Helper")
    print("=" * 40)
    
    # Load current .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ No .env file found. Please create one with required variables:")
        print_required_vars()
        return
    
    load_dotenv(env_file)
    print(f"✅ Found .env file: {env_file}")
    
    # Check required variables
    required_vars = {
        "SUPABASE_URL": "Supabase project URL",
        "SUPABASE_KEY": "Supabase service key (also accepts SUPABASE_SERVICE_KEY)"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if var == "SUPABASE_KEY":
            # Check both possible names
            if not (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")):
                missing_vars.append(f"{var} (or SUPABASE_SERVICE_KEY)")
        elif not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing required variables: {', '.join(missing_vars)}")
        print_required_vars()
        return
    
    print("\n✅ All required variables found!")
    
    # Check optional variables and suggest standardized names
    optional_mappings = {
        "OLLAMA_BASE_URL": "OLLAMA_URL",
        "OLLAMA_MODEL_NAME": "OLLAMA_MODEL", 
        "PROCESSING_CHUNK_SIZE": "CHUNK_SIZE",
        "PROCESSING_CHUNK_OVERLAP": "CHUNK_OVERLAP",
        "PROCESSING_MAX_FILE_SIZE_MB": "MAX_FILE_SIZE_MB",
        "PROCESSING_SUPPORTED_EXTENSIONS": "SUPPORTED_EXTENSIONS",
        "SUPABASE_TABLE_NAME": "SUPABASE_TABLE"
    }
    
    suggestions = []
    current_vars = {}
    
    for old_name, new_name in optional_mappings.items():
        old_value = os.getenv(old_name)
        new_value = os.getenv(new_name)
        
        if old_value and not new_value:
            suggestions.append(f"Consider renaming {old_name} to {new_name}")
            current_vars[new_name] = old_value
        elif new_value:
            current_vars[new_name] = new_value
        elif old_value:
            current_vars[old_name] = old_value
    
    if suggestions:
        print(f"\n💡 Optional improvements:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
    
    # Test the new configuration
    print(f"\n🧪 Testing new configuration system...")
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from config import Config
        
        config = Config()
        print("✅ New configuration system works!")
        
        print(f"\n📋 Current configuration:")
        config.print_summary()
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        print("Please check your .env file and try again.")
        return
    
    print(f"\n🎉 Migration check complete!")
    print(f"Your configuration is compatible with the new simplified system.")


def print_required_vars():
    """Print required environment variables."""
    print(f"\nRequired variables for .env file:")
    print(f"SUPABASE_URL=https://your-project.supabase.co")
    print(f"SUPABASE_KEY=your-service-key-here")
    print(f"\nOptional variables (with defaults):")
    print(f"SUPABASE_TABLE=documents")
    print(f"OLLAMA_URL=http://localhost:11434")
    print(f"OLLAMA_MODEL=nomic-embed-text")
    print(f"CHUNK_SIZE=1000")
    print(f"CHUNK_OVERLAP=200")
    print(f"MAX_FILE_SIZE_MB=100")
    print(f"SUPPORTED_EXTENSIONS=.txt")
    print(f"LOG_LEVEL=INFO")


if __name__ == "__main__":
    main()