#!/usr/bin/env python3
"""
Quick test commands for development workflow.
Usage: python test_commands.py <command>
"""

import sys
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

def run_cmd(cmd, description=""):
    """Run a command and show the result."""
    if description:
        print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0

def main():
    if len(sys.argv) < 2:
        print("""
🧪 Test Commands

Usage: python test_commands.py <command>

Available commands:
  unit          - Run unit tests only
  integration   - Run integration tests (mock)
  live          - Run live Supabase tests
  all           - Run all tests except live
  full          - Run everything including live tests
  coverage      - Run tests with coverage report
  quick         - Run fastest tests for development
  regression    - Full regression test suite
  
  # Specific test files
  storage       - Test storage adapter only
  config        - Test configuration only
  
  # Utilities  
  setup-check   - Check Supabase setup
  clean         - Clean test artifacts
        """)
        return

    command = sys.argv[1].lower()
    
    if command == "unit":
        run_cmd(["python", "-m", "pytest", "tests/unit/", "-v"], "Running unit tests")
    
    elif command == "integration":
        run_cmd(["python", "-m", "pytest", "tests/integration/", "-v", "-m", "not live"], "Running integration tests (mock)")
    
    elif command == "live":
        if not os.getenv("SUPABASE_URL"):
            print("❌ SUPABASE_URL not configured. Set up .env file first.")
            return
        run_cmd(["python", "-m", "pytest", "tests/integration/", "-v", "-m", "live", "-s"], "Running live tests")
    
    elif command == "all":
        run_cmd(["python", "-m", "pytest", "-v", "-m", "not live"], "Running all tests (except live)")
    
    elif command == "full":
        run_cmd(["python", "-m", "pytest", "-v"], "Running all tests including live")
    
    elif command == "coverage":
        run_cmd(["python", "-m", "pytest", "--cov=src", "--cov-report=html", "--cov-report=term"], "Running tests with coverage")
    
    elif command == "quick":
        run_cmd(["python", "-m", "pytest", "tests/unit/", "-x", "--tb=line"], "Running quick tests (fail fast)")
    
    elif command == "regression":
        run_cmd(["python", "run_regression_tests.py"], "Running full regression test suite")
    
    elif command == "storage":
        run_cmd(["python", "-m", "pytest", "-k", "storage", "-v"], "Running storage-related tests")
    
    elif command == "config":
        run_cmd(["python", "-m", "pytest", "-k", "config", "-v"], "Running configuration tests")
    
    elif command == "setup-check":
        run_cmd(["python", "check_supabase_setup.py"], "Checking Supabase setup")
    
    elif command == "clean":
        # Clean test artifacts
        import shutil
        artifacts = [".pytest_cache", "htmlcov", ".coverage", "__pycache__"]
        for artifact in artifacts:
            if os.path.exists(artifact):
                if os.path.isdir(artifact):
                    shutil.rmtree(artifact)
                else:
                    os.remove(artifact)
                print(f"🧹 Removed {artifact}")
        print("✅ Test artifacts cleaned")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python test_commands.py' for available commands")

if __name__ == "__main__":
    main()