#!/usr/bin/env python3
"""
Script to run live Supabase integration tests.

This script provides easy commands to test your live Supabase database.
"""

import sys
import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment.")
        return False
    
    print("✅ Environment variables configured")
    print(f"   SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
    print(f"   SUPABASE_TABLE: {os.getenv('SUPABASE_TABLE_NAME', 'documents')}")
    return True


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🚀 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main function to handle command line arguments."""
    if not check_environment():
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("""
🧪 Live Supabase Integration Test Runner

Usage: python run_live_tests.py <command>

Commands:
  health      - Test database connection and health
  basic       - Run basic storage and retrieval tests
  explore     - Explore current database contents
  sample      - Create sample document for manual exploration
  cleanup     - Clean up sample documents
  all         - Run all live tests
  similarity  - Test vector similarity search
  
Examples:
  python run_live_tests.py health
  python run_live_tests.py basic
  python run_live_tests.py explore
  python run_live_tests.py all
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    base_cmd = ["python", "-m", "pytest", "-v", "-s", "-m", "live"]
    
    if command == "health":
        cmd = base_cmd + ["tests/integration/test_live_supabase_integration.py::TestLiveSupabaseIntegration::test_live_database_connection"]
        run_command(cmd, "Testing database connection and health")
    
    elif command == "basic":
        cmd = base_cmd + [
            "tests/integration/test_live_supabase_integration.py::TestLiveSupabaseIntegration::test_live_database_connection",
            "tests/integration/test_live_supabase_integration.py::TestLiveSupabaseIntegration::test_live_document_storage_and_retrieval"
        ]
        run_command(cmd, "Running basic storage and retrieval tests")
    
    elif command == "explore":
        cmd = base_cmd + ["tests/integration/test_live_supabase_integration.py::TestLiveSupabaseExploration::test_explore_database_contents"]
        run_command(cmd, "Exploring current database contents")
    
    elif command == "sample":
        cmd = base_cmd + ["tests/integration/test_live_supabase_integration.py::TestLiveSupabaseExploration::test_create_sample_document"]
        run_command(cmd, "Creating sample document for manual exploration")
    
    elif command == "cleanup":
        cmd = base_cmd + ["tests/integration/test_live_supabase_integration.py::TestLiveSupabaseExploration::test_cleanup_sample_documents"]
        run_command(cmd, "Cleaning up sample documents")
    
    elif command == "similarity":
        cmd = base_cmd + ["tests/integration/test_live_supabase_integration.py::TestLiveSupabaseIntegration::test_live_vector_similarity_search"]
        run_command(cmd, "Testing vector similarity search")
    
    elif command == "all":
        cmd = base_cmd + ["tests/integration/test_live_supabase_integration.py::TestLiveSupabaseIntegration"]
        run_command(cmd, "Running all live integration tests")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python run_live_tests.py' for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()