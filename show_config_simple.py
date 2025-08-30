#!/usr/bin/env python3
"""Simple configuration display script using the new unified config."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from config import get_config
    
    print("Loading configuration...")
    config = get_config()
    config.print_summary()
    print("\n✅ Configuration loaded successfully!")
    
except Exception as e:
    print(f"❌ Configuration error: {e}")
    print("\nMake sure you have a .env file with required variables:")
    print("  SUPABASE_URL=https://your-project.supabase.co")
    print("  SUPABASE_KEY=your-service-key")
    sys.exit(1)