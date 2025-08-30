# 🧪 Simplified Vector Database Tests

This directory contains tests for the **simplified vector database architecture**. These tests are designed to be cleaner, faster, and easier to maintain than the original complex test suite.

## 📁 Test Structure

```
tests_simplified/
├── conftest.py              # Pytest fixtures and configuration
├── pytest.ini              # Pytest settings
├── README.md               # This file
├── test_config.py          # Configuration system tests
├── test_models.py          # Document model tests  
├── test_embedding.py       # Embedding client tests
├── test_storage.py         # Storage client tests
├── test_main.py            # Main VectorDB class tests
├── test_cli.py             # CLI interface tests
└── test_integration.py     # Integration tests
```

## 🎯 **Test Categories**

### **Unit Tests** (Fast, No External Dependencies)
- `test_config.py` - Configuration loading and validation
- `test_models.py` - Document model functionality
- `test_embedding.py` - Embedding client with mocked HTTP calls
- `test_storage.py` - Storage client with mocked Supabase calls
- `test_main.py` - VectorDB class with mocked dependencies
- `test_cli.py` - CLI commands with mocked VectorDB

### **Integration Tests** (Slower, May Require Live Services)
- `test_integration.py` - End-to-end workflows with real or mock services

## 🚀 **Running Tests**

### **Quick Start**
```bash
# Run all tests
python run_simplified_tests.py

# Run with verbose output
python run_simplified_tests.py --verbose

# Install dependencies and run tests
python run_simplified_tests.py --install-deps
```

### **Specific Test Types**
```bash
# Unit tests only (fast)
python run_simplified_tests.py --type unit

# Integration tests only (may require services)
python run_simplified_tests.py --type integration

# CLI tests only
python run_simplified_tests.py --type cli
```

### **Direct Pytest**
```bash
# Run all tests
pytest tests_simplified/

# Run specific test file
pytest tests_simplified/test_config.py

# Run with coverage
pytest tests_simplified/ --cov=vector_db --cov-report=term-missing

# Run only unit tests (skip integration)
pytest tests_simplified/ -m "not integration"
```

## 🔧 **Test Configuration**

### **Fixtures Available**
- `sample_document` - Single test document
- `sample_documents` - Multiple test documents
- `temp_text_file` - Temporary text file for testing
- `temp_directory` - Temporary directory with test files
- `mock_embedding_client` - Mocked embedding client
- `mock_storage_client` - Mocked storage client
- `mock_vector_db` - VectorDB with mocked dependencies

### **Test Markers**
- `@pytest.mark.integration` - Integration tests (may need live services)
- `@pytest.mark.unit` - Unit tests (fast, no external deps)
- `@pytest.mark.cli` - CLI-specific tests
- `@pytest.mark.slow` - Slow-running tests

## 📊 **Benefits Over Original Tests**

### **Simplified Structure**
| Aspect | Original Tests | Simplified Tests | Improvement |
|--------|---------------|------------------|-------------|
| **Files** | 15+ test files | 8 test files | **47% fewer files** |
| **Complexity** | High (adapters, ports, mocks) | Low (direct testing) | **Much simpler** |
| **Setup** | Complex fixtures | Simple fixtures | **Easier to understand** |
| **Speed** | Slow (complex setup) | Fast (minimal setup) | **Faster execution** |
| **Maintenance** | High | Low | **Easier to maintain** |

### **Key Improvements**
- ✅ **Direct testing** - Test actual functionality, not abstractions
- ✅ **Simpler mocking** - Mock only what's necessary
- ✅ **Better fixtures** - Reusable, focused fixtures
- ✅ **Clear separation** - Unit vs integration tests
- ✅ **CLI testing** - Comprehensive CLI test coverage
- ✅ **Integration workflows** - End-to-end testing

## 🎯 **Test Coverage**

### **What's Tested**
- ✅ **Configuration** - Loading, validation, environment variables
- ✅ **Document Models** - Creation, properties, methods
- ✅ **Embedding Client** - Generation, batching, error handling, retries
- ✅ **Storage Client** - CRUD operations, search, health checks
- ✅ **Main VectorDB** - File ingestion, directory processing, workflows
- ✅ **CLI Interface** - All commands, error handling, user interaction
- ✅ **Integration** - End-to-end workflows, service integration

### **Test Scenarios**
- ✅ **Success paths** - Normal operation
- ✅ **Error handling** - Network errors, invalid input, service failures
- ✅ **Edge cases** - Empty inputs, large files, duplicate content
- ✅ **Configuration** - Invalid settings, missing environment variables
- ✅ **CLI interaction** - User input, confirmation prompts, output formatting

## 🔍 **Example Test Run**

```bash
$ python run_simplified_tests.py --verbose

🧪 Running Simplified Vector Database Tests
============================================================
🎯 Running all tests...
📊 Coverage reporting enabled

========================= test session starts =========================
tests_simplified/test_config.py::TestSimplifiedConfig::test_config_loads_successfully PASSED
tests_simplified/test_config.py::TestSimplifiedConfig::test_config_validation PASSED
tests_simplified/test_models.py::TestDocument::test_document_creation PASSED
tests_simplified/test_models.py::TestDocument::test_content_preview_long PASSED
tests_simplified/test_embedding.py::TestEmbeddingClient::test_generate_embedding_success PASSED
tests_simplified/test_storage.py::TestStorageClient::test_store_document_success PASSED
tests_simplified/test_main.py::TestVectorDB::test_ingest_file_success PASSED
tests_simplified/test_cli.py::TestCLI::test_ingest_command_success PASSED
tests_simplified/test_integration.py::TestVectorDBIntegration::test_health_check_integration PASSED

========================= 45 passed in 2.34s =========================

============================================================
✅ All tests passed!
```

## 🛠 **Development Workflow**

### **Adding New Tests**
1. **Choose the right file** - Add to existing test file or create new one
2. **Use appropriate fixtures** - Leverage existing fixtures when possible
3. **Mock external dependencies** - Keep unit tests fast and isolated
4. **Add integration tests** - For end-to-end workflows
5. **Update this README** - Document new test categories or fixtures

### **Test-Driven Development**
1. **Write failing test** - Define expected behavior
2. **Implement feature** - Make the test pass
3. **Refactor** - Improve code while keeping tests green
4. **Add edge cases** - Test error conditions and edge cases

### **Debugging Tests**
```bash
# Run single test with full output
pytest tests_simplified/test_main.py::TestVectorDB::test_ingest_file_success -v -s

# Run with debugger
pytest tests_simplified/test_main.py::TestVectorDB::test_ingest_file_success --pdb

# Run with coverage and show missing lines
pytest tests_simplified/ --cov=vector_db --cov-report=html
```

## 📈 **Migration from Original Tests**

If you're migrating from the original complex test structure:

1. **Identify core functionality** - What actually needs testing?
2. **Remove adapter abstractions** - Test direct implementations
3. **Simplify fixtures** - Use simple, focused fixtures
4. **Focus on behavior** - Test what the code does, not how it's structured
5. **Add CLI tests** - Test the user-facing interface

The simplified tests provide **better coverage** with **less complexity** and **faster execution**.