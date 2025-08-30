# Requirements Document

## Introduction

This feature involves simplifying the over-engineered hexagonal architecture of the Python CLI Vector Database application. The current implementation uses unnecessary abstraction layers (ports/adapters pattern) that add complexity without benefits for a simple CLI tool. The goal is to reduce code complexity by 70-80% while maintaining all core functionality, making the codebase more maintainable and easier to understand.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to remove unnecessary hexagonal architecture abstractions, so that the codebase is simpler and more maintainable for a CLI tool.

#### Acceptance Criteria

1. WHEN the ports/adapters pattern is removed THEN the system SHALL use direct service implementations instead of abstract interfaces
2. WHEN adapters are eliminated THEN the system SHALL directly use Supabase and Ollama clients without wrapper layers
3. WHEN the domain layer is simplified THEN the system SHALL use simple dataclasses instead of complex domain models
4. IF core functionality is affected THEN the system SHALL maintain all existing CLI commands and features
5. WHEN simplification is complete THEN the system SHALL have 70-80% fewer lines of code while preserving functionality

### Requirement 2

**User Story:** As a developer, I want to consolidate the project structure into a flat module layout, so that navigation and understanding of the codebase is straightforward.

#### Acceptance Criteria

1. WHEN the src/ directory structure is flattened THEN the system SHALL move all code to a single vector_db/ package
2. WHEN modules are consolidated THEN the system SHALL have separate files for cli.py, config.py, embedding.py, storage.py, and main.py
3. WHEN imports are updated THEN the system SHALL use direct imports without complex adapter hierarchies
4. IF existing functionality is preserved THEN the system SHALL maintain all current CLI commands and configuration options
5. WHEN restructuring is complete THEN the system SHALL have a maximum of 6 core Python files in the main package

### Requirement 3

**User Story:** As a developer, I want to eliminate unnecessary abstraction layers, so that the code is more direct and easier to debug.

#### Acceptance Criteria

1. WHEN StoragePort interface is removed THEN the system SHALL use Supabase client directly in storage operations
2. WHEN EmbeddingPort interface is removed THEN the system SHALL use Ollama HTTP client directly for embeddings
3. WHEN FileSystemPort interface is removed THEN the system SHALL use pathlib.Path operations directly
4. WHEN dependency injection container is removed THEN the system SHALL use simple constructor injection
5. WHEN abstractions are eliminated THEN the system SHALL maintain the same error handling and retry logic

### Requirement 4

**User Story:** As a developer, I want to simplify the configuration system, so that setup and maintenance is straightforward.

#### Acceptance Criteria

1. WHEN multiple config classes are consolidated THEN the system SHALL use a single Pydantic-based configuration class
2. WHEN environment variable handling is simplified THEN the system SHALL automatically load from .env files using Pydantic
3. WHEN validation is streamlined THEN the system SHALL use Pydantic's built-in validation instead of custom logic
4. IF configuration compatibility is maintained THEN the system SHALL support all existing environment variables
5. WHEN config simplification is complete THEN the system SHALL have 90% fewer configuration-related lines of code

### Requirement 5

**User Story:** As a developer, I want to maintain all existing functionality while simplifying the architecture, so that users experience no regression in features.

#### Acceptance Criteria

1. WHEN architecture is simplified THEN the system SHALL preserve all CLI commands (ingest, status, config validation)
2. WHEN code is consolidated THEN the system SHALL maintain document chunking and embedding generation capabilities
3. WHEN abstractions are removed THEN the system SHALL keep error handling, retry logic, and logging functionality
4. WHEN testing is updated THEN the system SHALL maintain test coverage for all core functionality
5. WHEN simplification is complete THEN the system SHALL pass all existing integration tests with the simplified architecture

### Requirement 6

**User Story:** As a developer, I want to update the testing structure to match the simplified architecture, so that tests are easier to write and maintain.

#### Acceptance Criteria

1. WHEN test structure is updated THEN the system SHALL organize tests to match the flat module structure
2. WHEN test complexity is reduced THEN the system SHALL use direct mocking instead of complex adapter mocks
3. WHEN integration tests are simplified THEN the system SHALL test the actual simplified services directly
4. IF test coverage is maintained THEN the system SHALL preserve all existing test scenarios
5. WHEN testing updates are complete THEN the system SHALL have 50% fewer test files while maintaining coverage