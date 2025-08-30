# Implementation Plan

- [x] 1. Create simplified package structure and configuration
  - Create the new `vector_db/` package directory with `__init__.py`
  - Implement unified Pydantic-based configuration in `vector_db/config.py`
  - Create simple dataclass models in `vector_db/models.py`
  - Write unit tests for configuration validation and model creation
  - _Requirements: 2.1, 2.2, 4.1, 4.2, 4.3_

- [ ] 2. Implement direct embedding service
  - Create `vector_db/embedding.py` with direct Ollama HTTP client integration
  - Implement async embedding generation methods without adapter abstractions
  - Add batch processing capabilities for multiple text chunks
  - Include health check functionality and proper error handling
  - Write unit tests with mocked HTTP responses for embedding service
  - _Requirements: 1.1, 1.2, 3.2, 5.2, 5.3_

- [ ] 3. Implement direct storage service
  - Create `vector_db/storage.py` with direct Supabase client integration
  - Implement document storage and retrieval methods without port abstractions
  - Add batch insertion capabilities for document chunks
  - Include duplicate detection using content hash lookup
  - Write unit tests with mocked Supabase client for storage operations
  - _Requirements: 1.1, 1.2, 3.1, 5.2, 5.3_

- [ ] 4. Create main application orchestration
  - Implement `vector_db/main.py` with VectorDB class for application logic
  - Add file reading, text chunking, and content hashing functionality
  - Implement document ingestion workflow coordinating embedding and storage services
  - Add directory processing capabilities for batch file ingestion
  - Include comprehensive error handling and result reporting
  - Write unit tests for main application logic with service mocking
  - _Requirements: 1.3, 5.1, 5.2, 5.3, 5.5_

- [ ] 5. Implement simplified CLI interface
  - Create `vector_db/cli.py` with Click-based command interface
  - Implement `ingest` command for single files and directories
  - Add `status` command for health checking all services
  - Include `config-show` command for displaying current configuration
  - Add proper async command handling and user-friendly output formatting
  - Write CLI tests using Click's testing utilities
  - _Requirements: 2.2, 2.3, 5.1, 5.5_

- [ ] 6. Update and consolidate test structure
  - Restructure tests to match flat module layout in simplified test files
  - Create `tests/test_config.py` for configuration validation testing
  - Create `tests/test_embedding.py` for embedding service testing with mocks
  - Create `tests/test_storage.py` for storage service testing with mocks
  - Create `tests/test_main.py` for main application logic testing
  - Create `tests/test_cli.py` for CLI command testing
  - Update `tests/conftest.py` with simplified fixtures and utilities
  - _Requirements: 6.1, 6.2, 6.4, 6.5_

- [ ] 7. Create integration tests for simplified architecture
  - Implement `tests/test_integration.py` for end-to-end workflow testing
  - Test complete document ingestion pipeline with real or mocked services
  - Verify CLI commands work correctly with the simplified architecture
  - Add performance and error handling validation in integration scenarios
  - Ensure all existing functionality is preserved in simplified implementation
  - _Requirements: 5.4, 5.5, 6.3, 6.4_

- [ ] 8. Remove old complex architecture files
  - Delete the entire `src/` directory with hexagonal architecture implementation
  - Remove old configuration files and utility scripts that are no longer needed
  - Clean up old test files that have been replaced by simplified test structure
  - Update import statements in any remaining files to use new module structure
  - Verify no broken imports or references to deleted modules remain
  - _Requirements: 1.1, 1.4, 2.1, 2.3_

- [ ] 9. Update project configuration and documentation
  - Update `requirements.txt` to include only necessary dependencies (remove unused packages)
  - Create or update `pyproject.toml` with proper package configuration for simplified structure
  - Update README.md to reflect simplified architecture and usage instructions
  - Update any example scripts to use the new simplified module imports
  - Ensure all documentation matches the new simplified implementation
  - _Requirements: 2.4, 5.4_

- [ ] 10. Validate complete functionality and run comprehensive tests
  - Run all unit tests to ensure simplified implementation works correctly
  - Execute integration tests to verify end-to-end functionality is preserved
  - Test CLI commands manually to confirm user experience is maintained
  - Verify configuration loading and validation works with environment variables
  - Confirm embedding generation and storage operations function as expected
  - Run performance comparison to ensure no significant regression in simplified code
  - _Requirements: 1.5, 5.1, 5.4, 5.5, 6.4, 6.5_