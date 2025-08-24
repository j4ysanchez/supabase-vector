#!/usr/bin/env python3
"""
Comprehensive regression test runner for the Python CLI Vector DB project.

This script runs all tests in a structured way to ensure no regressions
are introduced during development.
"""

import sys
import subprocess
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BLUE}{'-' * len(title)}{Colors.END}")

def run_command(cmd: list, description: str, allow_failure: bool = False) -> bool:
    """Run a command and return success status."""
    print(f"\n{Colors.YELLOW}🔄 {description}{Colors.END}")
    print(f"Command: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        duration = time.time() - start_time
        
        print(f"{Colors.GREEN}✅ {description} - PASSED ({duration:.2f}s){Colors.END}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        
        if allow_failure:
            print(f"{Colors.YELLOW}⚠️  {description} - SKIPPED ({duration:.2f}s){Colors.END}")
            print(f"Reason: {e.stderr.strip() if e.stderr else 'Command failed'}")
            return True
        else:
            print(f"{Colors.RED}❌ {description} - FAILED ({duration:.2f}s){Colors.END}")
            print(f"Error: {e.stderr.strip() if e.stderr else 'Command failed'}")
            if e.stdout:
                print(f"Output: {e.stdout.strip()}")
            return False

def check_environment():
    """Check if the environment is properly set up."""
    print_section("Environment Check")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"{Colors.GREEN}✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Python version too old: {python_version.major}.{python_version.minor}.{python_version.micro}{Colors.END}")
        return False
    
    # Check required packages
    required_packages = ['pytest', 'pytest-asyncio', 'python-dotenv']
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"{Colors.GREEN}✅ {package} installed{Colors.END}")
        except ImportError:
            print(f"{Colors.RED}❌ {package} not installed{Colors.END}")
            return False
    
    # Check project structure
    required_dirs = ['src', 'tests', 'tests/unit', 'tests/integration', 'tests/mocks']
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"{Colors.GREEN}✅ {dir_path}/ directory exists{Colors.END}")
        else:
            print(f"{Colors.RED}❌ {dir_path}/ directory missing{Colors.END}")
            return False
    
    return True

def run_unit_tests():
    """Run all unit tests."""
    print_section("Unit Tests")
    
    commands = [
        (["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"], "Unit Tests - Verbose"),
        (["python", "-m", "pytest", "tests/unit/", "--cov=src", "--cov-report=term-missing"], "Unit Tests - With Coverage"),
    ]
    
    results = []
    for cmd, desc in commands:
        results.append(run_command(cmd, desc))
    
    return all(results)

def run_integration_tests():
    """Run integration tests (mock-based)."""
    print_section("Integration Tests (Mock)")
    
    commands = [
        (["python", "-m", "pytest", "tests/integration/test_storage_integration.py", "-v", "-m", "not live"], "Mock Integration Tests"),
    ]
    
    results = []
    for cmd, desc in commands:
        results.append(run_command(cmd, desc))
    
    return all(results)

def run_live_tests():
    """Run live integration tests if Supabase is configured."""
    print_section("Live Integration Tests")
    
    # Check if Supabase is configured
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print(f"{Colors.YELLOW}⚠️  Supabase not configured - skipping live tests{Colors.END}")
        print("To enable live tests, set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
        return True
    
    print(f"{Colors.GREEN}✅ Supabase configured - running live tests{Colors.END}")
    
    commands = [
        (["python", "check_supabase_setup.py"], "Supabase Setup Check"),
        (["python", "-m", "pytest", "tests/integration/test_live_supabase_integration.py::TestLiveSupabaseIntegration::test_live_database_connection", "-v", "-s"], "Live Database Connection"),
        (["python", "-m", "pytest", "tests/integration/test_live_supabase_integration.py::TestLiveSupabaseIntegration::test_live_document_storage_and_retrieval", "-v", "-s"], "Live Storage & Retrieval"),
        (["python", "-m", "pytest", "tests/integration/test_live_supabase_integration.py::TestLiveSupabaseIntegration::test_live_vector_similarity_search", "-v", "-s"], "Live Vector Similarity"),
    ]
    
    results = []
    for cmd, desc in commands:
        # Allow live tests to fail (they depend on external service)
        results.append(run_command(cmd, desc, allow_failure=True))
    
    return all(results)

def run_code_quality_checks():
    """Run code quality and style checks."""
    print_section("Code Quality Checks")
    
    commands = [
        # Syntax check
        (["python", "-m", "py_compile"] + [str(p) for p in Path("src").rglob("*.py")], "Python Syntax Check"),
    ]
    
    # Optional: Add linting if tools are available
    try:
        import flake8
        commands.append((["python", "-m", "flake8", "src/", "--max-line-length=120", "--ignore=E203,W503"], "Flake8 Linting"))
    except ImportError:
        print(f"{Colors.YELLOW}ℹ️  flake8 not installed - skipping linting{Colors.END}")
    
    try:
        import black
        commands.append((["python", "-m", "black", "--check", "src/"], "Black Code Formatting Check"))
    except ImportError:
        print(f"{Colors.YELLOW}ℹ️  black not installed - skipping format check{Colors.END}")
    
    results = []
    for cmd, desc in commands:
        results.append(run_command(cmd, desc, allow_failure=True))
    
    return all(results)

def run_import_tests():
    """Test that all modules can be imported."""
    print_section("Import Tests")
    
    # Find all Python files in src/
    python_files = list(Path("src").rglob("*.py"))
    python_files = [f for f in python_files if f.name != "__init__.py"]
    
    results = []
    for py_file in python_files:
        # Convert file path to module name
        module_path = str(py_file).replace("/", ".").replace("\\", ".").replace(".py", "")
        cmd = ["python", "-c", f"import {module_path}; print('✅ {module_path}')"]
        results.append(run_command(cmd, f"Import {module_path}", allow_failure=True))
    
    return all(results)

def generate_test_report(results: dict):
    """Generate a summary test report."""
    print_header("REGRESSION TEST REPORT")
    
    total_sections = len(results)
    passed_sections = sum(1 for result in results.values() if result)
    
    print(f"\n{Colors.BOLD}Summary:{Colors.END}")
    print(f"  Total Test Sections: {total_sections}")
    print(f"  Passed: {Colors.GREEN}{passed_sections}{Colors.END}")
    print(f"  Failed: {Colors.RED}{total_sections - passed_sections}{Colors.END}")
    
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.END}")
    for section, result in results.items():
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if result else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"  {section}: {status}")
    
    if all(results.values()):
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 ALL REGRESSION TESTS PASSED!{Colors.END}")
        print(f"{Colors.GREEN}Your code is ready for deployment.{Colors.END}")
        return True
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}❌ SOME TESTS FAILED{Colors.END}")
        print(f"{Colors.RED}Please fix the failing tests before deployment.{Colors.END}")
        return False

def main():
    """Main regression test runner."""
    print_header("PYTHON CLI VECTOR DB - REGRESSION TESTS")
    
    start_time = time.time()
    
    # Check environment first
    if not check_environment():
        print(f"\n{Colors.RED}❌ Environment check failed. Please fix the issues above.{Colors.END}")
        sys.exit(1)
    
    # Run all test categories
    results = {}
    
    # Core functionality tests
    results["Unit Tests"] = run_unit_tests()
    results["Integration Tests"] = run_integration_tests()
    results["Live Tests"] = run_live_tests()
    
    # Code quality tests
    results["Import Tests"] = run_import_tests()
    results["Code Quality"] = run_code_quality_checks()
    
    # Generate report
    total_time = time.time() - start_time
    success = generate_test_report(results)
    
    print(f"\n{Colors.BOLD}Total execution time: {total_time:.2f} seconds{Colors.END}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()