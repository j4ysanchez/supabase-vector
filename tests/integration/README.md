# Integration Tests for Supabase Vector Storage

This directory contains comprehensive integration tests for the Supabase vector storage functionality. These tests verify that the storage adapter works correctly with the database schema and handles various scenarios including error conditions.

## Test Coverage

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