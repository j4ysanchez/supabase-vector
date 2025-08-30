# 🧪 Vector Database Tests

This directory contains the **simplified test suite** for the Python CLI Vector Database project. These tests replace the previous complex architecture with a clean, maintainable approach.

## 📁 Test Structure

```
tests/
├── conftest.py          # Pytest fixtures and configuration
├── test_config.py       # Configuration system tests
├── test_embedding.py    # Ollama embedding tests
├── test_storage.py      # Supabase storage tests
├── test_cli.py          # CLI interface tests
├── test_main.py         # Main VectorDB class tests
└── README.md           # This file
```

## 🎯 Test Categories

### Unit Tests (Fast, No External Dependencies)
- **test_config.py** - Configuration loading and validation
- **test_embedding.py** - Embedding generation with mocked HTTP calls
- **test_storage.py** - Document storage with mocked Supabase client
- **test_cli.py** - CLI commands with mocked dependencies
- **test_main.py** - VectorDB class with mocked services

### Integration Tests (Require Live Services)
- Tests marked with `@pytest.mark.integration`
- Tests marked with `@pytest.mark.live`

## 🚀 Running Tests

### Simple Test Runner
```bash
# Run all tests
python run_tests.py all

# Run only unit tests (fast)
python run_tests.py unit

# Run integration tests (requires services)
python run_tests.py integration

# Run live tests (requires real Supabase/Ollama)
python run_tests.py live

# Run with coverage report
python run_tests.py coverage
```

### Direct Pytest
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py

# Run only unit tests
pytest -m unit

# Run with coverage
pytest --cov=vector_db --cov-report=html
```

## 🔧 Available Fixtures

- **test_config** - Test configuration with safe defaults
- **temp_file** - Temporary test file with cleanup
- **mock_supabase_client** - Mocked Supabase client
- **mock_ollama_client** - Mocked Ollama HTTP client
- **storage_service** - Storage service with mocked client
- **embedding_service** - Embedding service with mocked client

## 📊 Simplification Benefits

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Test Files** | 15+ files | 5 files | **67% reduction** |
| **Test Runners** | 5 scripts | 1 script | **80% reduction** |
| **Complexity** | High | Low | **Much simpler** |
| **Maintenance** | Difficult | Easy | **Easier to maintain** |
| **Speed** | Slow | Fast | **Faster execution** |

## 🎯 What's Tested

### Configuration System
- Environment variable loading
- Default values
- Validation and type conversion
- Error handling

### Embedding Service
- Successful embedding generation
- HTTP error handling
- Invalid response handling
- Empty text handling

### Storage Service
- Document storage and retrieval
- Search functionality
- Error handling
- Health checks

### CLI Interface
- All commands (ingest, search, status)
- Help text
- Error handling
- File validation

### Main Application
- Document ingestion workflow
- Search functionality
- Status reporting
- Error handling

## 🔍 Example Test Run

```bash
$ python run_tests.py unit

🧪 Running unit tests...
========================= test session starts =========================
tests/test_config.py::test_config_from_env PASSED
tests/test_config.py::test_config_defaults PASSED
tests/test_embedding.py::test_generate_embedding_success PASSED
tests/test_storage.py::test_store_document_success PASSED
tests/test_cli.py::test_cli_help PASSED
tests/test_main.py::test_vector_db_init PASSED

========================= 25 passed in 1.23s =========================
```

## 🛠 Development Workflow

### Adding New Tests
1. Choose the appropriate test file
2. Use existing fixtures when possible
3. Mock external dependencies for unit tests
4. Add integration tests for end-to-end workflows

### Test-Driven Development
1. Write failing test first
2. Implement minimal code to pass
3. Refactor while keeping tests green
4. Add edge cases and error conditions

### Debugging Tests
```bash
# Run single test with verbose output
pytest tests/test_main.py::test_vector_db_init -v -s

# Run with debugger
pytest tests/test_main.py::test_vector_db_init --pdb

# Show coverage gaps
pytest --cov=vector_db --cov-report=term-missing
```

## 📈 Migration Notes

This simplified test structure replaces:
- Complex hexagonal architecture tests
- Multiple test runners and utilities
- Scattered test files at project root
- Over-engineered mocking and fixtures

The new approach provides:
- ✅ Better test coverage
- ✅ Faster test execution
- ✅ Easier maintenance
- ✅ Clearer test organization
- ✅ Simpler debugging