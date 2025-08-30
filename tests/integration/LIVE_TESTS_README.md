# Live End-to-End Integration Tests

This directory contains live integration tests that demonstrate and validate the complete embedding storage workflow using real Ollama and Supabase services.

## Overview

The live tests demonstrate the complete pipeline:
1. **Text Input** → **Ollama Embedding Generation** → **Supabase Vector Storage** → **Similarity Search**

## Test Files

### `test_live_end_to_end_demo.py` ⭐ **RECOMMENDED**
- **Purpose**: Comprehensive demonstration of the live workflow
- **Features**: 
  - Automatic service detection and fallback to mocks
  - Clear setup instructions
  - Detailed step-by-step output
  - Works with or without live services
- **Run**: `pytest tests/integration/test_live_end_to_end_demo.py -v -s`

### `test_live_end_to_end_embedding_storage.py`
- **Purpose**: Comprehensive live testing with multiple scenarios
- **Features**: 
  - Multiple test scenarios (single doc, similarity search, multi-chunk, performance)
  - Requires live services to be available
  - More detailed testing scenarios
- **Run**: `pytest tests/integration/test_live_end_to_end_embedding_storage.py -v -s -m live`

### `test_live_supabase_integration.py`
- **Purpose**: Supabase-specific live integration tests
- **Features**: 
  - Database exploration tools
  - Manual data inspection
  - Supabase-specific functionality testing
- **Run**: `pytest tests/integration/test_live_supabase_integration.py -v -s -m live`

## Prerequisites

### 1. Ollama Setup
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the embedding model
ollama pull nomic-embed-text

# Start Ollama service (usually runs automatically)
# Default URL: http://localhost:11434
```

### 2. Supabase Setup
1. Create a Supabase project at https://supabase.com/
2. Run the database migrations:
   ```bash
   # Navigate to your project root
   cd /path/to/your/project
   
   # Run migrations (if using Supabase CLI)
   supabase db push
   
   # Or manually run the SQL files in migrations/ folder
   ```
3. Get your project URL and service role key from the Supabase dashboard

### 3. Environment Configuration
Create or update your `.env` file:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=nomic-embed-text
OLLAMA_TIMEOUT=60
OLLAMA_MAX_RETRIES=3

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
SUPABASE_TABLE_NAME=documents
SUPABASE_TIMEOUT=30
SUPABASE_MAX_RETRIES=3
```

## Running the Tests

### Quick Start (Recommended)
```bash
# Run the demo test - works with or without live services
pytest tests/integration/test_live_end_to_end_demo.py -v -s

# Check requirements and get setup instructions
pytest tests/integration/test_live_end_to_end_demo.py::TestLiveEndToEndWorkflowDemo::test_live_workflow_requirements_check -v -s
```

### Full Live Testing
```bash
# Run all live tests (requires live services)
pytest tests/integration/ -v -s -m live

# Run specific live test scenarios
pytest tests/integration/test_live_end_to_end_embedding_storage.py::TestLiveEndToEndEmbeddingStorageWorkflow::test_complete_live_workflow -v -s -m live
```

### Mock Mode Testing
If you don't have live services set up, the demo test will automatically use mock services:
```bash
# Temporarily disable live services to see mock mode
unset OLLAMA_BASE_URL SUPABASE_URL SUPABASE_SERVICE_KEY
pytest tests/integration/test_live_end_to_end_demo.py::TestLiveEndToEndWorkflowDemo::test_live_workflow_with_services -v -s
```

## Expected Output

### Live Services Mode
```
🧪 Live End-to-End Workflow Test
==================================================
🌐 Using LIVE services:
   Ollama: http://localhost:11434
   Supabase: https://your-project.supabase.co

🔄 Step 1: Testing service health...
   Ollama health: ✅ Healthy
   Supabase health: ✅ Healthy

🔄 Step 2: Generating embedding with Ollama...
   ✅ Generated embedding:
      Dimensions: 768
      First 5 values: [0.613, 1.584, -2.923, -1.267, 0.157]
      Norm: 17.972

🔄 Step 3: Creating document...
   ✅ Document created: live_demo_20240101_120000.txt

🔄 Step 4: Storing document in Supabase...
   ✅ Document stored successfully!
      Document ID: 12345678-1234-1234-1234-123456789abc

🔄 Step 5: Retrieving document...
   ✅ Document retrieved successfully!
      Filename: live_demo_20240101_120000.txt
      Chunks: 1
      Content length: 336
      Embedding similarity: 1.000000

🔄 Step 6: Testing similarity search...
   ✅ Similarity search test:
      Query: vector database embedding storage workflow
      Similarity to stored document: 0.798
      Supabase similarity search found 1 results
         1. live_demo_20240101_120000.txt (similarity: 0.798)

🎉 LIVE END-TO-END WORKFLOW COMPLETED SUCCESSFULLY!
   ✅ Ollama embedding generation: Working
   ✅ Supabase vector storage: Working
   ✅ Document retrieval: Working
   ✅ Similarity search: Working
   ✅ Data integrity: Verified
```

## Troubleshooting

### Ollama Issues
- **Service not running**: Start Ollama service
- **Model not found**: Run `ollama pull nomic-embed-text`
- **Connection refused**: Check if `OLLAMA_BASE_URL` is correct
- **Timeout errors**: Increase `OLLAMA_TIMEOUT` in environment

### Supabase Issues
- **Connection failed**: Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- **Table not found**: Run database migrations
- **Permission denied**: Use service role key, not anon key
- **Schema errors**: Check that vector extension is enabled

### General Issues
- **Environment variables**: Ensure `.env` file is in project root
- **Dependencies**: Run `pip install -r requirements.txt`
- **Network issues**: Check firewall and network connectivity

## Test Scenarios Covered

### 1. Complete Workflow (`test_complete_live_workflow`)
- Text → Embedding → Storage → Retrieval → Verification
- Tests data integrity and embedding preservation
- Validates metadata handling

### 2. Similarity Search (`test_live_similarity_search`)
- Multiple documents with different content types
- Semantic similarity ranking
- Supabase similarity function testing

### 3. Multi-chunk Processing (`test_live_multi_chunk_processing`)
- Document chunking and individual embedding generation
- Chunk-level similarity search
- Multi-chunk storage and retrieval

### 4. Performance Testing (`test_live_performance_batch_processing`)
- Batch embedding generation
- Concurrent storage operations
- Performance metrics and timing

## Database Exploration

The live tests also provide tools for exploring your Supabase database:

```bash
# Explore current database contents
pytest tests/integration/test_live_supabase_integration.py::TestLiveSupabaseExploration::test_explore_database_contents -v -s

# Create sample data for manual exploration
pytest tests/integration/test_live_supabase_integration.py::TestLiveSupabaseExploration::test_create_sample_document -v -s

# Clean up sample data
pytest tests/integration/test_live_supabase_integration.py::TestLiveSupabaseExploration::test_cleanup_sample_documents -v -s
```

## Integration with CI/CD

For continuous integration, you can:

1. **Skip live tests by default**:
   ```bash
   pytest -m "not live"
   ```

2. **Run live tests in specific environments**:
   ```bash
   # Only run if environment variables are set
   if [ -n "$OLLAMA_BASE_URL" ] && [ -n "$SUPABASE_URL" ]; then
       pytest -m live
   fi
   ```

3. **Use the demo test for validation**:
   ```bash
   # Always works - uses mocks if live services unavailable
   pytest tests/integration/test_live_end_to_end_demo.py
   ```

## Contributing

When adding new live tests:

1. Use the `@pytest.mark.live` decorator
2. Include service health checks
3. Provide clear error messages and troubleshooting hints
4. Clean up test data in `finally` blocks
5. Support both live and mock modes when possible

## Security Notes

- Never commit real service keys to version control
- Use environment variables for all sensitive configuration
- Use service role keys for testing, not production keys
- Consider using separate test databases/projects for live testing