#!/usr/bin/env python3
"""Test runner for the simplified vector database tests."""

import subprocess
import sys
from pathlib import Path


def run_tests(test_type="all", verbose=False):
    """Run the simplified tests.
    
    Args:
        test_type: Type of tests to run ("all", "unit", "integration", "cli")
        verbose: Whether to run in verbose mode
    """
    print("🧪 Running Simplified Vector Database Tests")
    print("=" * 60)
    
    # Base pytest command
    cmd = ["python", "-m", "pytest", "tests_simplified/"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add test type filter
    if test_type == "unit":
        cmd.extend(["-m", "not integration"])
        print("📋 Running unit tests only...")
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
        print("🔗 Running integration tests only...")
    elif test_type == "cli":
        cmd.append("tests_simplified/test_cli.py")
        print("💻 Running CLI tests only...")
    else:
        print("🎯 Running all tests...")
    
    # Add coverage if available
    try:
        import coverage
        cmd.extend(["--cov=vector_db", "--cov-report=term-missing"])
        print("📊 Coverage reporting enabled")
    except ImportError:
        print("ℹ️  Coverage not available (install with: pip install pytest-cov)")
    
    print()
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=False)
        
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run simplified vector database tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "cli"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run in verbose mode"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true", 
        help="Install test dependencies first"
    )
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("📦 Installing test dependencies...")
        deps = ["pytest", "pytest-asyncio", "pytest-cov", "click"]
        for dep in deps:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
                print(f"   ✅ Installed {dep}")
            except subprocess.CalledProcessError:
                print(f"   ❌ Failed to install {dep}")
        print()
    
    # Check if tests directory exists
    if not Path("tests_simplified").exists():
        print("❌ tests_simplified directory not found!")
        print("   Make sure you're running this from the project root.")
        return 1
    
    # Run tests
    return run_tests(args.type, args.verbose)


if __name__ == "__main__":
    sys.exit(main())