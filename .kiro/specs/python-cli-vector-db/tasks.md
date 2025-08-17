# Implementation Plan

- [ ] 1. Set up project structure and core domain models
  - Create directory structure following hexagonal architecture (domain/, ports/, adapters/, application/, infrastructure/)
  - Define core domain models (Document, DocumentChunk, ProcessingResult) with proper typing
  - Implement basic value objects and domain exceptions
  - _Requirements: 1.1, 5.2, 5.3_

- [ ] 2. Implement domain services for business logic
  - [ ] 2.1 Create DocumentProcessor domain service
    - Implement document chunking logic with configurable size and overlap
    - Add content hashing functionality for duplicate detection
    - Write unit tests for chunking edge cases and hash generation
    - _Requirements: 5.1, 5.4_

  - [ ] 2.2 Create EmbeddingOrchestrator domain service  
    - Implement orchestration logic for embedding generation and storage
    - Add batch processing capabilities for efficiency
    - Write unit tests with mock ports for isolation testing
    - _Requirements: 1.2, 1.3, 4.4_

- [ ] 3. Define secondary ports (interfaces)
  - [ ] 3.1 Create StoragePort interface
    - Define abstract methods for document storage, retrieval, and health checks
    - Include type hints and comprehensive docstrings
    - Add error handling specifications in interface documentation
    - _Requirements: 1.3, 4.2_

  - [ ] 3.2 Create EmbeddingPort interface
    - Define abstract methods for embedding generation and health checks
    - Specify batch processing capabilities in interface
    - Document expected input/output formats and error conditions
    - _Requirements: 1.2, 4.1_

  - [ ] 3.3 Create FileSystemPort interface
    - Define abstract methods for file reading and directory listing
    - Include path validation and error handling specifications
    - Add support for filtering .txt files in directory operations
    - _Requirements: 1.1, 3.3_

- [ ] 4. Implement secondary adapters
  - [ ] 4.1 Create SupabaseStorageAdapter
    - Implement StoragePort interface using Supabase Python client
    - Add connection management, retry logic with exponential backoff
    - Implement upsert logic for handling duplicate documents
    - Write integration tests with test database
    - _Requirements: 1.3, 2.1, 4.2, 5.4_

  - [ ] 4.2 Create OllamaEmbeddingAdapter
    - Implement EmbeddingPort interface using httpx for async HTTP calls
    - Add proper error handling for network failures and API errors
    - Implement batch processing for multiple text inputs
    - Write unit tests with mocked HTTP responses
    - _Requirements: 1.2, 2.1, 4.1, 4.3_

  - [ ] 4.3 Create LocalFileSystemAdapter
    - Implement FileSystemPort interface for local file operations
    - Add proper error handling for file access permissions and missing files
    - Implement recursive directory traversal for .txt files
    - Write unit tests with temporary test files
    - _Requirements: 1.1, 3.3, 4.1_

- [ ] 5. Create application services layer
  - [ ] 5.1 Define primary port (DocumentIngestionPort interface)
    - Create interface for application-level operations (ingest file/directory, health check)
    - Define comprehensive error handling and return types
    - Document expected behavior and error conditions
    - _Requirements: 3.1, 3.2, 3.4_

  - [ ] 5.2 Implement DocumentIngestionService
    - Implement DocumentIngestionPort using domain services and secondary ports
    - Add comprehensive error handling and logging throughout the service
    - Implement progress reporting for batch operations
    - Write unit tests using mock secondary ports
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.4_

- [ ] 6. Implement configuration and dependency injection
  - [ ] 6.1 Create configuration management system
    - Define typed configuration classes for all external services
    - Implement environment variable loading with validation
    - Add support for .env files and configuration validation
    - Write tests for configuration loading and validation scenarios
    - _Requirements: 2.1, 2.2, 2.4_

  - [ ] 6.2 Create dependency injection container
    - Implement DIContainer class to wire up all dependencies
    - Add factory methods for creating configured service instances
    - Implement proper lifecycle management for connections
    - Write tests for dependency resolution and configuration
    - _Requirements: 2.1, 2.2, 2.3_

- [ ] 7. Implement CLI primary adapter
  - [ ] 7.1 Create CLI command structure using Click
    - Implement main CLI entry point with proper command organization
    - Add global options for configuration and logging
    - Implement help text and usage examples for all commands
    - _Requirements: 3.1, 3.4_

  - [ ] 7.2 Implement ingest command
    - Create ingest command that accepts file or directory paths
    - Add progress reporting and error handling for user feedback
    - Implement verbose mode for detailed operation logging
    - Write integration tests for CLI command execution
    - _Requirements: 3.2, 3.3, 4.4_

  - [ ] 7.3 Implement utility commands (config, status)
    - Create config check command to validate configuration
    - Implement status command to check service health
    - Add proper error reporting and user-friendly messages
    - Write tests for all CLI commands and error scenarios
    - _Requirements: 2.4, 3.4_

- [ ] 8. Add comprehensive error handling and logging
  - [ ] 8.1 Implement custom exception hierarchy
    - Create domain-specific exceptions for different error types
    - Add proper error context and user-friendly messages
    - Implement error recovery strategies where appropriate
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 8.2 Add structured logging throughout application
    - Configure logging with appropriate levels and formatters
    - Add contextual logging in all major operations
    - Implement log correlation for tracking operations across components
    - _Requirements: 4.4, 4.5_

- [ ] 9. Create database schema and migrations
  - [ ] 9.1 Create Supabase database schema
    - Write SQL migration scripts for documents table with vector support
    - Add proper indexes for performance (vector similarity, filename, hash)
    - Implement Row Level Security policies for data protection
    - _Requirements: 1.3, 5.2, 5.3_

  - [ ] 9.2 Add database initialization utilities
    - Create scripts to set up database schema and extensions
    - Add validation utilities to check database configuration
    - Implement migration management for schema updates
    - _Requirements: 2.1, 2.3_

- [ ] 10. Implement comprehensive testing suite
  - [ ] 10.1 Create unit tests for domain layer
    - Write comprehensive tests for DocumentProcessor and EmbeddingOrchestrator
    - Test all edge cases for document chunking and processing logic
    - Ensure 100% test coverage for business logic components
    - _Requirements: 1.1, 1.2, 5.1, 5.4_

  - [ ] 10.2 Create integration tests for adapters
    - Write integration tests for Supabase adapter with test database
    - Test Ollama adapter with mock server or test instance
    - Create end-to-end tests for complete ingestion workflow
    - _Requirements: 1.3, 2.1, 4.2_

- [ ] 11. Add project packaging and documentation
  - [ ] 11.1 Create proper Python package structure
    - Set up pyproject.toml with dependencies and build configuration
    - Create entry points for CLI commands
    - Add package metadata and version management
    - _Requirements: 3.1_

  - [ ] 11.2 Write comprehensive documentation
    - Create README with installation and usage instructions
    - Document configuration options and environment variables
    - Add examples for common use cases and troubleshooting guide
    - _Requirements: 2.4, 3.4_