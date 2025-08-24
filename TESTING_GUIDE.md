# Testing Guide

This guide explains how to run the different types of tests in the Python CLI Vector DB project.

## Test Structure Overview

The project uses a comprehensive testing strategy with multiple test types:

```
tests/
├── unit/                    # Unit tests (fast, isolated)
├── integration/             # Integration tests (mock-based)
├── mocks/                   # Mock implementations
├── factories/               # Test object factories
└── fixtures/                # Test data and fixtures
```

## Test Types

### 1. Unit Tests
**Purpose**: Test individual components in isolation with all dependencies mocked.

**Location**: `tests/unit/`

**Characteristics**:
- Fast execution (< 1 second per test)
- No external dependencies
- High code coverage
- Test business logic and edge cases

**Run Commands**:
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage report
pytest tests/unit/ --cov=src --cov-report=term-missing

# Run specific unit test file
pytest tests/unit/adapters/test_supabase_storage_adapter.py -v
```

### 2. Integration Tests (Mock-based)
**Purpose**: Test component interactions using mocks to simulate external services.

**Location**: `tests/integration/`

**Characteristics**:
- Medium execution time (1-5 seconds per test)
- Uses `MockSupabaseClient` for database simulation
- Tests end-to-end workflows without external dependencies
- Validates component integration

**Run Commands**:
```bash
# Run all mock integration tests
pytest tests/integration/ -v -m "not live"

# Run specific integration test
pytest tests/integration/test_storage_integration.py -v

# Run with detailed output
pytest tests/integration/ -v -s
```

### 3. Live Integration Tests
**Purpose**: Test against real Supabase database to validate actual functionality.

**Location**: `tests/integration/test_live_supabase_integration.py`

**Characteristics**:
- Slower execution (5-30 seconds per test)
- Requires Supabase configuration
- Tests real database operations
- Validates production-like scenarios

**Prerequisites**:
```bash
# Set up environment variables in .env file
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_TABLE_NAME=documents
```

**Run Commands**:
```bash
# Check Supabase setup first
python check_supabase_setup.py

# Run all live tests
pytest tests/integration/ -v -m "live"

# Run specific live test
pytest tests/integration/test_live_supabase_integration.py::TestLiveSupabaseIntegration::test_live_database_connection -v

# Run live tests with output
pytest tests/integration/ -v -s -m "live"
```

## Quick Test Commands

### Development Workflow
```bash
# Quick smoke test (fastest)
pytest tests/unit/ -x --tb=line

# Standard development test
pytest tests/unit/ tests/integration/ -v -m "not live"

# Full test suite (including live tests)
pytest -v
```

### Continuous Integration
```bash
# Run regression test suite
python run_regression_tests.py

# CI-friendly command (no live tests)
pytest tests/ -v -m "not live" --cov=src --cov-report=xml
```

### Debugging Tests
```bash
# Run with detailed output and stop on first failure
pytest tests/unit/ -v -s -x

# Run specific test with full traceback
pytest tests/unit/adapters/test_supabase_storage_adapter.py::TestSupabaseStorageAdapter::test_store_document -v -s --tb=long

# Run tests matching pattern
pytest -k "test_storage" -v
```

## Test Markers

The project uses pytest markers to categorize tests:

```bash
# Run only unit tests
pytest -m "unit"

# Run only integration tests
pytest -m "integration"

# Skip live tests (default for CI)
pytest -m "not live"

# Run only smoke tests (quick validation)
pytest -m "smoke"

# Skip slow tests
pytest -m "not slow"
```

## Coverage Reports

### Generate Coverage Reports
```bash
# Terminal coverage report
pytest tests/ --cov=src --cov-report=term-missing -m "not live"

# HTML coverage report
pytest tests/ --cov=src --cov-report=html -m "not live"
open htmlcov/index.html

# XML coverage report (for CI)
pytest tests/ --cov=src --cov-report=xml -m "not live"
```

### Coverage Configuration
Coverage is configured in `pytest.ini`:
- **Source**: `src/` directory
- **Omitted**: `*/tests/*`, `*/venv/*`, `*/__pycache__/*`
- **Target**: 80%+ coverage for production code

## Test Data and Fixtures

### Mock Data
Tests use realistic but synthetic data:
- 768-dimensional vector embeddings
- Structured document metadata
- Unique identifiers for isolation

### Test Factories
Located in `tests/factories/`, these create test objects:
```python
from tests.factories.storage_factory import create_mock_storage_adapter

# Create adapter with mock client
adapter = create_mock_storage_adapter("https://test.supabase.co", "test-key", "test_table")
```

## Environment Setup

### Required Dependencies
```bash
pip install pytest pytest-asyncio pytest-cov python-dotenv
```

### Optional Development Tools
```bash
pip install flake8 black mypy  # Code quality tools
```

### Environment Variables
Create `.env` file for live tests:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
SUPABASE_TABLE_NAME=documents
```

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure PYTHONPATH includes src/
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# Or run from project root
cd /path/to/project
pytest tests/
```

**2. Async Test Issues**
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Check pytest.ini has asyncio_mode = auto
```

**3. Live Test Failures**
```bash
# Check Supabase setup
python check_supabase_setup.py

# Verify environment variables
python -c "import os; print(os.getenv('SUPABASE_URL'))"
```

**4. Coverage Issues**
```bash
# Ensure source path is correct
pytest --cov=src --cov-report=term-missing

# Check pytest.ini coverage configuration
```

## Best Practices

### Test Development
1. **Write unit tests first** - Fast feedback loop
2. **Use mocks for external dependencies** - Reliable and fast
3. **Test edge cases and error conditions** - Robust error handling
4. **Keep tests independent** - No shared state between tests
5. **Use descriptive test names** - Clear intent and purpose

### Test Execution
1. **Run unit tests frequently** - During development
2. **Run integration tests before commits** - Catch integration issues
3. **Run live tests before releases** - Validate production readiness
4. **Use markers to control test execution** - Efficient CI/CD pipelines

### Maintenance
1. **Keep mocks synchronized with real APIs** - Accurate simulation
2. **Update tests when requirements change** - Maintain test relevance
3. **Monitor test execution time** - Keep feedback loops fast
4. **Review coverage reports regularly** - Identify untested code

## Integration with IDEs

### VS Code
Add to `.vscode/settings.json`:
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests/",
        "-v",
        "-m", "not live"
    ]
}
```

### PyCharm
1. Go to Settings → Tools → Python Integrated Tools
2. Set Default test runner to pytest
3. Set pytest arguments: `-v -m "not live"`

## Automated Testing

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Add to .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        args: [tests/, -v, -m, "not live"]
```

### GitHub Actions
Example workflow for CI:
```yaml
- name: Run tests
  run: |
    pytest tests/ -v -m "not live" --cov=src --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

This testing strategy ensures code quality, reliability, and maintainability while providing fast feedback during development.