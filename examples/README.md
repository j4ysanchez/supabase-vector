# Embedding Demo

This directory contains demonstration scripts for the vector database embedding functionality.

## Embedding Demo (`embedding_demo.py`)

The embedding demo showcases how to use the OllamaEmbeddingAdapter to generate text embeddings using a local Ollama service.

### Prerequisites

1. **Ollama Service**: You need Ollama running locally
   ```bash
   # Install Ollama (macOS)
   brew install ollama
   
   # Start Ollama service
   ollama serve
   ```

2. **Embedding Model**: Install the nomic-embed-text model
   ```bash
   ollama pull nomic-embed-text
   ```

3. **Python Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

The demo uses environment variables for configuration. You can either:

1. **Set environment variables manually:**
   ```bash
   export OLLAMA_BASE_URL="http://localhost:11434"
   export OLLAMA_MODEL_NAME="nomic-embed-text"
   export OLLAMA_TIMEOUT="30"
   export OLLAMA_MAX_RETRIES="3"
   export OLLAMA_BATCH_SIZE="32"
   ```

2. **Use a `.env` file** (recommended):
   The demo automatically loads the `.env` file from the project root. Make sure your `.env` file contains:
   ```bash
   # Ollama Configuration
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL_NAME=nomic-embed-text:latest
   OLLAMA_TIMEOUT=60
   OLLAMA_MAX_RETRIES=3
   OLLAMA_BATCH_SIZE=32
   ```
   
   **Note**: Use the full model name with tag (e.g., `nomic-embed-text:latest`) as it appears in `ollama list`.

3. **Use defaults**: The demo will use sensible defaults if no environment variables are set.

### Running the Demo

```bash
# From the project root directory
python examples/embedding_demo.py

# Alternative: if you get import errors, try:
PYTHONPATH=. python examples/embedding_demo.py
```

### What the Demo Does

The embedding demo demonstrates:

1. **Configuration Loading**: Loads Ollama settings from environment variables
2. **Health Check**: Verifies that Ollama is running and the model is available
3. **Single Embedding**: Generates an embedding for a single text string
4. **Batch Embeddings**: Generates embeddings for multiple texts at once
5. **Statistics**: Shows embedding dimensions and sample values
6. **Error Handling**: Demonstrates proper error handling and logging

### Expected Output

```
2025-08-30 09:00:20,488 - __main__ - INFO - Loading environment variables from /path/to/project/.env
2025-08-30 09:00:20,489 - __main__ - INFO - Environment configuration:
2025-08-30 09:00:20,489 - __main__ - INFO -   OLLAMA_BASE_URL: http://localhost:11434
2025-08-30 09:00:20,489 - __main__ - INFO -   OLLAMA_MODEL_NAME: nomic-embed-text:latest
2025-08-30 09:00:20,489 - __main__ - INFO -   OLLAMA_TIMEOUT: 60
2025-08-30 09:00:20,489 - __main__ - INFO -   OLLAMA_MAX_RETRIES: 3
2025-08-30 09:00:20,489 - __main__ - INFO -   OLLAMA_BATCH_SIZE: 32
2025-08-30 09:00:20,490 - __main__ - INFO - Starting Ollama Embedding Demo
2025-08-30 09:00:20,490 - __main__ - INFO - Loading Ollama configuration...
2025-08-30 09:00:20,490 - __main__ - INFO - Using Ollama at: http://localhost:11434
2025-08-30 09:00:20,490 - __main__ - INFO - Model: nomic-embed-text:latest
2025-08-30 09:00:20,536 - __main__ - INFO - Created OllamaEmbeddingAdapter
2025-08-30 09:00:20,536 - __main__ - INFO - Performing health check...
2025-08-30 09:00:20,570 - __main__ - INFO - ✓ Ollama service is healthy
2025-08-30 09:00:20,571 - __main__ - INFO - Embedding dimension: 768
2025-08-30 09:00:20,571 - __main__ - INFO - Generating embedding for single text...
2025-08-30 09:00:20,933 - __main__ - INFO - Generated embedding with 768 dimensions
2025-08-30 09:00:20,933 - __main__ - INFO - First 5 values: [0.097, 1.502, -3.500, -1.562, 1.179]
2025-08-30 09:00:20,933 - __main__ - INFO - Generating embeddings for multiple texts...
2025-08-30 09:00:21,073 - __main__ - INFO - Generated 4 embeddings
2025-08-30 09:00:21,073 - __main__ - INFO - Text 1: avg=0.0041, len=768
2025-08-30 09:00:21,073 - __main__ - INFO -   'The quick brown fox jumps over the lazy dog....'
2025-08-30 09:00:21,073 - __main__ - INFO - Text 2: avg=0.0054, len=768
2025-08-30 09:00:21,073 - __main__ - INFO -   'Machine learning is a subset of artificial intelli...'
2025-08-30 09:00:21,073 - __main__ - INFO - Text 3: avg=0.0042, len=768
2025-08-30 09:00:21,073 - __main__ - INFO -   'Vector databases enable semantic search capabiliti...'
2025-08-30 09:00:21,073 - __main__ - INFO - Text 4: avg=0.0059, len=768
2025-08-30 09:00:21,073 - __main__ - INFO -   'Python is a popular programming language for data ...'
2025-08-30 09:00:21,073 - __main__ - INFO - ✓ Demo completed successfully
```

### Troubleshooting

#### Import Errors
```
ModuleNotFoundError: No module named 'src'
```

**Solution**: 
1. Make sure you're running from the project root directory
2. Try using: `PYTHONPATH=. python examples/embedding_demo.py`
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

#### Ollama Service Not Running
```
ERROR - Ollama service is not healthy. Please check:
ERROR - 1. Ollama is running
ERROR - 2. The nomic-embed-text model is available
ERROR - 3. The service is accessible at the configured URL
```

**Solution**: 
1. Start Ollama: `ollama serve`
2. Install the model: `ollama pull nomic-embed-text`
3. Check the service: `curl http://localhost:11434/api/tags`

#### Connection Errors
```
ERROR - Embedding error: Failed to connect to Ollama: Network error: Connection failed
```

**Solution**: 
1. Verify Ollama is running on the correct port
2. Check firewall settings
3. Verify the `OLLAMA_BASE_URL` environment variable

#### Model Not Available
```
WARNING - Model 'nomic-embed-text' not found in available models: ['nomic-embed-text:latest', 'llama2', 'codellama']
```

**Solution**: 
1. Install the model: `ollama pull nomic-embed-text`
2. Use the full model name with tag: `OLLAMA_MODEL_NAME=nomic-embed-text:latest`
3. Check available models: `ollama list`
4. Or change to an available model: `export OLLAMA_MODEL_NAME="your-model-name:tag"`

### Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service URL |
| `OLLAMA_MODEL_NAME` | `nomic-embed-text` | Embedding model name |
| `OLLAMA_TIMEOUT` | `30` | Request timeout (seconds) |
| `OLLAMA_MAX_RETRIES` | `3` | Maximum retry attempts |
| `OLLAMA_BATCH_SIZE` | `32` | Batch size for processing |

### Next Steps

After running the demo successfully, you can:

1. **Integrate with your application**: Use the `OllamaEmbeddingAdapter` in your own code
2. **Run the tests**: See `tests/README.md` for testing instructions
3. **Explore other models**: Try different embedding models available in Ollama
4. **Scale up**: Adjust batch sizes and timeouts for production workloads