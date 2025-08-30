#!/usr/bin/env python3
"""
Simplified test runner for the vector database project.
Replaces all the complex test runners with a simple interface.
"""
import subprocess
import sys
from pathlib import Path


def run_unit_tests():
    """Run only unit tests (fast, no external dependencies)."""
    print("🧪 Running unit tests...")
    return subprocess.run([
        sys.executable, "-m", "pytest", 
        "-m", "unit",
        "--tb=short"
    ]).returncode


def run_integration_tests():
    """Run integration tests (require external services)."""
    print("🔗 Running integration tests...")
    return subprocess.run([
        sys.executable, "-m", "pytest", 
        "-m", "integration",
        "--tb=short"
    ]).returncode


def run_live_tests():
    """Run live tests (require real Supabase/Ollama)."""
    print("🌐 Running live tests...")
    return subprocess.run([
        sys.executable, "-m", "pytest", 
        "-m", "live",
        "--tb=short"
    ]).returncode


def run_all_tests():
    """Run all tests."""
    print("🚀 Running all tests...")
    return subprocess.run([
        sys.executable, "-m", "pytest",
        "--tb=short"
    ]).returncode


def run_coverage():
    """Run tests with coverage report."""
    print("📊 Running tests with coverage...")
    return subprocess.run([
        sys.executable, "-m", "pytest",
        "--cov=vector_db",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--tb=short"
    ]).returncode


def main():
    """Main test runner interface."""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [unit|integration|live|all|coverage]")
        print()
        print("Commands:")
        print("  unit        - Run unit tests only (fast)")
        print("  integration - Run integration tests (requires services)")
        print("  live        - Run live tests (requires real Supabase/Ollama)")
        print("  all         - Run all tests")
        print("  coverage    - Run tests with coverage report")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "unit":
        exit_code = run_unit_tests()
    elif command == "integration":
        exit_code = run_integration_tests()
    elif command == "live":
        exit_code = run_live_tests()
    elif command == "all":
        exit_code = run_all_tests()
    elif command == "coverage":
        exit_code = run_coverage()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()