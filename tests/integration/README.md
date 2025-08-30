# Integration Tests

This directory contains comprehensive integration tests for both Supabase vector storage and Ollama embedding generation functionality. These tests verify that the adapters work correctly with their respective services and handle various scenarios including error conditions.

## Test Files

- `test_storage_integration.py` - Supabase vector storage integration tests
- `test_ollama_integration.py` - Ollama embedding generation integration tests  
- `test_live_supabase_integration.py` - Live Supabase integration tests (requires actual database)

## Ollama Integration Tests

The Ollama integration tests (`test_ollama_integration.py`) provide comprehensive coverage for the Ollama embedding adapter, fulfilling the requirements specified in task 2.2.

### Ollama Test Coverage

#### 1. Service Connection and Model Availability

**Test**: `test_service_connection_and_model_availability`
- Verifies connection to Ollama service via health check
- Confirms required model (nomic-embed-text) is available
- Tests proper API response parsing for model listing

**Test**: `test_service_connection_model_not_available`
- Tests health check when required model is not available
- Verifies proper handling when model list doesn't include required model

**Test**: `test_service_connection_failure`
- Tests health check when Ollama service is completely unavailable
- Verifies graceful handling of connection errors

**Test**: `test_service_http_error_response`
- Tests health check with various HTTP error responses (404, 500, etc.)
- Verifies proper error handling for API failures

#### 2. Embedding Generation and Vector Dimensions

**Test**: `test_single_text_embedding_generation`
- Tests embedding generation for single text input
- Verifies embedding produces expected 768 dimensions (nomic-embed-text)
- Confirms embedding values are properly formatted as float lists

**Test**: `test_multiple_text_embedding_generation`
- Tests embedding generation for multiple text inputs
- Verifies each text produces correct dimensional embeddings
- Tests that different texts produce different embeddings

**Test**: `test_empty_text_list_handling`
- Tests proper handling of empty input lists
- Verifies no API calls are made for empty inputs

**Test**: `test_unexpected_embedding_dimension`
- Tests adapter behavior when model returns unexpected dimensions
- Verifies adapter adapts to actual embedding dimensions dynamically

#### 3. Batch Processing for Multiple Text Inputs

**Test**: `test_batch_processing_within_limit`
- Tests batch processing when all texts fit within configured batch size
- Verifies proper sequencing of API calls for batch processing

**Test**: `test_batch_processing_exceeds_limit`
- Tests batch processing when input exceeds configured batch size
- Verifies proper batching and sequencing across multiple API calls

**Test**: `test_large_batch_processing`
- Tests efficient processing of large batches (20+ texts)
- Verifies performance and proper handling of extended processing

#### 4. Error Scenarios (Service Unavailable, Invalid Model)

**Test**: `test_service_unavailable_error`
- Tests handling when Ollama service is completely unavailable
- Verifies proper EmbeddingError propagation with original error context
- Tests retry mechanism behavior with persistent failures

**Test**: `test_http_error_responses`
- Tests handling of various HTTP error responses (404, 500, etc.)
- Verifies proper error message formatting and context preservation

**Test**: `test_invalid_response_format`
- Tests handling of malformed API responses (missing 'embedding' field)
- Verifies proper error detection and reporting

**Test**: `test_invalid_embedding_format`
- Tests handling of invalid embedding formats (non-list, wrong types)
- Verifies proper validation and error reporting

**Test**: `test_empty_embedding_response`
- Tests handling of empty embedding arrays in responses
- Verifies proper validation of embedding content

**Test**: `test_retry_mechanism_with_transient_errors`
- Tests retry mechanism with transient network errors
- Verifies exponential backoff and eventual success after retries

**Test**: `test_retry_exhaustion`
- Tests behavior when all retry attempts are exhausted
- Verifies proper error reporting after maximum retries

**Test**: `test_timeout_error_handling`
- Tests handling of request timeout errors
- Verifies proper timeout error classification and reporting

#### 5. Configuration and Initialization

**Test**: `test_adapter_initialization_with_valid_config`
- Tests proper adapter initialization with valid configuration
- Verifies all configuration parameters are properly set

**Test**: `test_adapter_with_custom_client`
- Tests adapter initialization with custom HTTP client
- Verifies proper client injection and usage

**Test**: `test_config_validation_missing_base_url`
- Tests configuration validation with missing required fields
- Verifies proper ConfigValidationError raising

**Test**: `test_config_validation_invalid_url_format`
- Tests configuration validation with invalid URL formats
- Verifies proper URL format validation

**Test**: `test_config_validation_invalid_numeric_values`
- Tests configuration validation with invalid numeric parameters
- Verifies proper numeric validation and error reporting

## Supabase Storage Test Coverage

### 1. Database Connection and Table Structure Verification

**Test**: `test_database_connection_and_table_structure`
- Verifies basic connectivity to Supabase
- Confirms table structure is accessible
- Tests health check functionality
- Validates that the adapter can initialize properly

**Test**: `test_table_schema_validation`
- Tests storage of documents with all expected schema fields
- Verifies 768-dimensional vector embeddings are supported
- Confirms all metadata fields are preserved
- Tests retrieval of stored documents with full schema

### 2. Document Storage and Retrieval with Vector Embeddings

**Test**: `test_document_storage_and_retrieval`
- Tests complete document lifecycle (store → retrieve → verify)
- Verifies vector embeddings are stored and retrieved correctly
- Confirms metadata separation between document and chunk levels
- Tests data integrity across storage/retrieval operations

**Test**: `test_find_by_content_hash`
- Tests duplicate detection using content hashes
- Verifies hash-based document lookup functionality
- Tests behavior with non-existent hashes

**Test**: `test_document_listing_with_pagination`
- Tests document listing with pagination support
- Verifies batch operations work correctly
- Tests pagination boundaries and limits

### 3. Vector Similarity Search Functionality

**Test**: `test_vector_similarity_search_functionality`
- Tests vector similarity calculations using cosine similarity
- Verifies that similar embeddings can be identified
- Tests with known similar and dissimilar vector pairs
- Validates embedding retrieval for similarity comparisons

**Test**: `test_vector_embedding_integrity`
- Tests high-precision embedding value preservation
- Verifies 768-dimensional vector storage accuracy
- Tests floating-point precision maintenance

### 4. Error Scenarios and Edge Cases

**Test**: `test_connection_failure_scenarios`
- Tests behavior with invalid Supabase URLs
- Verifies graceful handling of connection failures
- Tests health check failure scenarios

**Test**: `test_invalid_data_scenarios`
- Tests handling of invalid embedding dimensions
- Verifies error handling for malformed data
- Tests graceful degradation with invalid inputs

**Test**: `test_nonexistent_document_operations`
- Tests retrieval of non-existent documents
- Tests deletion of non-existent documents
- Tests search for non-existent content hashes

**Test**: `test_storage_error_handling`
- Tests proper exception propagation
- Verifies StorageError handling
- Tests edge cases with empty or invalid content

**Test**: `test_concurrent_operations`
- Tests concurrent document storage operations
- Verifies thread safety and race condition handling
- Tests concurrent retrieval and deletion operations

### 5. Configuration and Environment Tests

**Test**: `test_configuration_validation`
- Tests configuration validation logic
- Verifies required field validation
- Tests invalid configuration scenarios

**Test**: `test_environment_configuration_loading`
- Tests loading configuration from environment variables
- Verifies environment variable precedence
- Tests missing environment variable handling

## Test Architecture

### Mock vs Real Testing

The integration tests use a `MockSupabaseClient` that simulates Supabase operations for testing purposes. This approach provides several benefits:

1. **Deterministic Testing**: Tests run consistently without external dependencies
2. **Error Simulation**: Can simulate various error conditions reliably
3. **Performance**: Tests run quickly without network overhead
4. **Isolation**: Tests don't interfere with real databases

### Test Data Management

- Tests create isolated test data with unique identifiers
- All tests clean up after themselves (delete created documents)
- Test documents use realistic 768-dimensional embeddings
- Metadata is structured to test both document and chunk-level data

### Vector Similarity Testing

The tests include mathematical verification of vector similarity using numpy's cosine similarity calculation. This ensures that:

- Similar vectors have high similarity scores (> 0.8)
- Dissimilar vectors have low similarity scores (< 0.5)
- Vector operations maintain mathematical correctness

## Running the Tests

### Prerequisites

```bash
pip install -r requirements.txt
```

### Run All Integration Tests

```bash
python -m pytest tests/integration/ -v
```

### Run Specific Test Categories

```bash
# Database connection tests
python -m pytest tests/integration/test_storage_integration.py::TestSupabaseVectorStorageIntegration::test_database_connection_and_table_structure -v

# Vector similarity tests
python -m pytest tests/integration/test_storage_integration.py::TestSupabaseVectorStorageIntegration::test_vector_similarity_search_functionality -v

# Error scenario tests
python -m pytest tests/integration/test_storage_integration.py::TestSupabaseVectorStorageIntegration::test_connection_failure_scenarios -v
```

### Test Output

The tests provide detailed output including:
- Test execution status and timing
- Assertion failures with detailed comparisons
- Error messages and stack traces for debugging
- Coverage of all major code paths

## Requirements Verification

### Ollama Integration Tests (Task 2.2)

These integration tests fulfill the requirements specified in task 2.2:

✅ **Test connection to Ollama service and model availability**
- `TestOllamaServiceConnection` class with comprehensive connection tests
- Health check validation with model availability verification
- Error handling for service unavailability and HTTP errors

✅ **Verify embedding generation produces expected vector dimensions**
- `TestEmbeddingGeneration` class with dimension validation tests
- Verification of 768-dimensional embeddings for nomic-embed-text
- Dynamic adaptation to unexpected embedding dimensions

✅ **Test batch processing for multiple text inputs**
- `TestBatchProcessing` class with comprehensive batch processing tests
- Tests for within-limit, exceeding-limit, and large batch scenarios
- Verification of proper API call sequencing and efficiency

✅ **Add tests for error scenarios (service unavailable, invalid model)**
- `TestErrorScenarios` class with extensive error handling tests
- Service unavailability, HTTP errors, invalid responses, timeouts
- Retry mechanism testing with transient and persistent errors
- Configuration validation and initialization error testing

The tests cover Requirements 1.2 (embedding generation), 4.1 (error handling), and 4.3 (service integration) as specified in the task details.

### Supabase Storage Integration Tests (Task 1.4)

These integration tests fulfill the requirements specified in task 1.4:

✅ **Create test that connects to Supabase and verifies table structure**
- `test_database_connection_and_table_structure`
- `test_table_schema_validation`

✅ **Test storing and retrieving documents with vector embeddings**
- `test_document_storage_and_retrieval`
- `test_vector_embedding_integrity`
- `test_document_listing_with_pagination`

✅ **Verify vector similarity search functionality works correctly**
- `test_vector_similarity_search_functionality`
- Mathematical verification using cosine similarity

✅ **Add tests for error scenarios (connection failures, invalid data)**
- `test_connection_failure_scenarios`
- `test_invalid_data_scenarios`
- `test_nonexistent_document_operations`
- `test_storage_error_handling`
- `test_concurrent_operations`

The tests cover Requirements 1.3 (vector storage) and 4.2 (error handling) as specified in the task details.