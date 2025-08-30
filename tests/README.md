# Testing Guide for Embedding Functionality

This guide covers how to run tests for the embedding functionality, including unit tests, integration tests, and comprehensive test suites.

## Quick Start

```bash
# Run all embedding-related tests
python -m pytest tests/ -k "embedding" -v

# Run only unit tests for embeddings
python -m pytest tests/unit/adapters/test_ollama_embedding_adapter.py -v

# Run only integration tests for embeddings
python -m pytest tests/integration/test_ollama_integration.py -v
```

## Test Structure

```
tests/
├── unit/
│   └── adapters/
│       └── test_ollama_embedding_adapter.py    # Unit tests for OllamaEmbeddingAdapter
├── integration/
│   └── test_ollama_integration.py              # Integration tests with mocked HTTP
└── README.md                                   # This file
```

## Unit Tests

### OllamaEmbeddingAdapter Unit Tests

**File**: `tests/unit/adapters/test_ollama_embedding_adapter.py`

These tests verify the core functionality of the OllamaEmbeddingAdapter without making actual HTTP requests.

#### Running Unit Tests

```bash
# Run all unit tests for the embedding adapter
python -m pytest tests/unit/adapters/test_ollama_embedding_adapter.py -v

# Run specific test methods
python -m pytest tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_generate_embedding_success -v

# Run with coverage
python -m pytest tests/unit/adapters/test_ollama_embedding_adapter.py --cov=src.adapters.secondary.ollama --cov-report=html
```

#### Test Coverage

The unit tests cover:

- ✅ **Successful embedding generation** (single and batch)
- ✅ **Empty input handling**
- ✅ **HTTP error handling** (4xx, 5xx responses)
- ✅ **Network error handling** (connection failures)
- ✅ **Invalid response format handling**
- ✅ **Retry logic with exponential backoff**
- ✅ **Maximum retry limit enforcement**
- ✅ **Health check functionality**
- ✅ **Model availability verification**
- ✅ **Resource management** (async context manager)
- ✅ **Configuration handling**

#### Expected Output

```bash
$ python -m pytest tests/unit/adapters/test_ollama_embedding_adapter.py -v

================================================== test session starts ===================================================
collected 14 items

tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_generate_embedding_success PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_generate_embeddings_batch PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_generate_embeddings_empty_list PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_generate_embedding_http_error PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_generate_embedding_network_error PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_generate_embedding_invalid_response PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_generate_embedding_retry_logic PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_generate_embedding_max_retries_exceeded PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_health_check_success PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_health_check_model_not_available PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_health_check_connection_error PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_get_embedding_dimension PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_context_manager PASSED
tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_close PASSED

================================================== 14 passed in 15.06s ===================================================
```

## Integration Tests

### Ollama Integration Tests

**File**: `tests/integration/test_ollama_integration.py`

These tests verify the integration behavior with mocked HTTP responses, simulating real-world scenarios.

#### Running Integration Tests

```bash
# Run all integration tests for embeddings
python -m pytest tests/integration/test_ollama_integration.py -v

# Run specific integration test
python -m pytest tests/integration/test_ollama_integration.py::TestOllamaIntegration::test_embedding_generation_with_mock_server -v
```

#### Test Coverage

The integration tests cover:

- ✅ **Adapter initialization and configuration**
- ✅ **End-to-end embedding generation workflow**
- ✅ **Health check integration**
- ✅ **Batch processing behavior**
- ✅ **Error handling in integration context**

#### Expected Output

```bash
$ python -m pytest tests/integration/test_ollama_integration.py -v

================================================== test session starts ===================================================
collected 5 items

tests/integration/test_ollama_integration.py::TestOllamaIntegration::test_embedding_adapter_initialization PASSED
tests/integration/test_ollama_integration.py::TestOllamaIntegration::test_embedding_generation_with_mock_server PASSED
tests/integration/test_ollama_integration.py::TestOllamaIntegration::test_health_check_with_mock_server PASSED
tests/integration/test_ollama_integration.py::TestOllamaIntegration::test_batch_processing PASSED
tests/integration/test_ollama_integration.py::TestOllamaIntegration::test_error_handling_integration PASSED

=================================================== 5 passed in 1.10s ====================================================
```

## Comprehensive Test Commands

### Run All Embedding Tests

```bash
# All embedding-related tests (unit + integration)
python -m pytest tests/ -k "embedding" -v

# With coverage report
python -m pytest tests/ -k "embedding" --cov=src.adapters.secondary.ollama --cov=src.ports.secondary.embedding_port --cov-report=html
```

### Run Tests by Category

```bash
# Unit tests only
python -m pytest tests/unit/ -k "embedding" -v

# Integration tests only
python -m pytest tests/integration/ -k "embedding" -v

# All adapter tests (including storage)
python -m pytest tests/unit/adapters/ -v
python -m pytest tests/integration/ -v
```

### Run Tests with Different Output Formats

```bash
# Verbose output with test names
python -m pytest tests/ -k "embedding" -v

# Short summary
python -m pytest tests/ -k "embedding" -q

# Show only failures
python -m pytest tests/ -k "embedding" --tb=short

# Show test durations
python -m pytest tests/ -k "embedding" --durations=10
```

## Test Configuration

### Prerequisites

No external services are required for these tests as they use mocked HTTP clients. However, you need:

1. **Python Dependencies**:
   ```bash
   pip install pytest pytest-asyncio pytest-cov httpx
   ```

2. **Project Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

The tests don't require environment variables as they use test configurations, but you can set them for consistency:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL_NAME="nomic-embed-text"
```

## Test Development

### Adding New Tests

When adding new embedding functionality, follow these patterns:

#### Unit Test Example

```python
@pytest.mark.asyncio
async def test_new_functionality(self, adapter, mock_client):
    """Test description."""
    # Arrange
    mock_response = Mock()
    mock_response.json.return_value = {"expected": "response"}
    mock_client.post.return_value = mock_response
    
    # Act
    result = await adapter.new_method()
    
    # Assert
    assert result == expected_result
    mock_client.post.assert_called_once()
```

#### Integration Test Example

```python
@pytest.mark.asyncio
async def test_new_integration_scenario(self, ollama_config):
    """Test integration scenario."""
    mock_client = httpx.AsyncClient()
    
    async def mock_post(url, **kwargs):
        # Mock implementation
        pass
    
    mock_client.post = mock_post
    
    async with OllamaEmbeddingAdapter(ollama_config, mock_client) as adapter:
        result = await adapter.new_method()
        assert result == expected_result
```

### Test Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies** (HTTP clients, file systems)
4. **Test both success and failure scenarios**
5. **Use fixtures** for common setup code
6. **Add docstrings** to explain complex test scenarios

## Continuous Integration

### GitHub Actions Example

```yaml
name: Embedding Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/ -k "embedding" --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: embedding-tests
        name: Run embedding tests
        entry: python -m pytest tests/ -k "embedding" -q
        language: system
        pass_filenames: false
```

## Troubleshooting

### Common Issues

#### Import Errors
```
ModuleNotFoundError: No module named 'src'
```
**Solution**: Run tests from the project root directory

#### Async Test Issues
```
RuntimeError: There is no current event loop
```
**Solution**: Ensure `pytest-asyncio` is installed and tests use `@pytest.mark.asyncio`

#### Mock Issues
```
AttributeError: Mock object has no attribute 'aclose'
```
**Solution**: Use `AsyncMock` for async methods and specify the correct spec

### Debug Mode

Run tests with debug output:

```bash
# Enable debug logging
python -m pytest tests/ -k "embedding" -v -s --log-cli-level=DEBUG

# Drop into debugger on failure
python -m pytest tests/ -k "embedding" --pdb

# Run specific test with maximum verbosity
python -m pytest tests/unit/adapters/test_ollama_embedding_adapter.py::TestOllamaEmbeddingAdapter::test_generate_embedding_success -vvv -s
```

## Performance Testing

For performance testing of the embedding functionality:

```bash
# Run tests with timing
python -m pytest tests/ -k "embedding" --durations=0

# Profile test execution
python -m pytest tests/ -k "embedding" --profile

# Memory usage profiling
python -m pytest tests/ -k "embedding" --memray
```

This comprehensive testing approach ensures the embedding functionality is robust, reliable, and ready for production use.