#!/usr/bin/env python3
"""
Demo script showing how to use the OllamaEmbeddingAdapter.

This script demonstrates:
1. Loading configuration from environment variables
2. Creating an OllamaEmbeddingAdapter instance
3. Performing health checks
4. Generating embeddings for text
5. Proper error handling and resource cleanup

Prerequisites:
- Ollama service running locally (default: http://localhost:11434)
- nomic-embed-text model available in Ollama
- Environment variables set (see .env.example)

Usage:
    python examples/embedding_demo.py
"""

import asyncio
import logging
import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adapters.secondary.ollama.ollama_embedding_adapter import OllamaEmbeddingAdapter
from src.infrastructure.config.ollama_config import OllamaConfig
from src.domain.exceptions import EmbeddingError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main demo function."""
    logger.info("Starting Ollama Embedding Demo")
    
    try:
        # Load configuration from environment
        logger.info("Loading Ollama configuration...")
        config = OllamaConfig.from_env()
        logger.info(f"Using Ollama at: {config.base_url}")
        logger.info(f"Model: {config.model_name}")
        
        # Create adapter instance
        async with OllamaEmbeddingAdapter(config) as adapter:
            logger.info("Created OllamaEmbeddingAdapter")
            
            # Perform health check
            logger.info("Performing health check...")
            is_healthy = await adapter.health_check()
            
            if not is_healthy:
                logger.error("Ollama service is not healthy. Please check:")
                logger.error("1. Ollama is running")
                logger.error("2. The nomic-embed-text model is available")
                logger.error("3. The service is accessible at the configured URL")
                return
            
            logger.info("✓ Ollama service is healthy")
            
            # Get embedding dimension
            dimension = adapter.get_embedding_dimension()
            logger.info(f"Embedding dimension: {dimension}")
            
            # Test single embedding generation
            logger.info("Generating embedding for single text...")
            test_text = "This is a test sentence for embedding generation."
            
            embedding = await adapter.generate_embedding(test_text)
            logger.info(f"Generated embedding with {len(embedding)} dimensions")
            logger.info(f"First 5 values: {embedding[:5]}")
            
            # Test batch embedding generation
            logger.info("Generating embeddings for multiple texts...")
            test_texts = [
                "The quick brown fox jumps over the lazy dog.",
                "Machine learning is a subset of artificial intelligence.",
                "Vector databases enable semantic search capabilities.",
                "Python is a popular programming language for data science."
            ]
            
            embeddings = await adapter.generate_embeddings(test_texts)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Show some statistics
            for i, (text, emb) in enumerate(zip(test_texts, embeddings)):
                avg_value = sum(emb) / len(emb)
                logger.info(f"Text {i+1}: avg={avg_value:.4f}, len={len(emb)}")
                logger.info(f"  '{text[:50]}...'")
            
            logger.info("✓ Demo completed successfully")
            
    except EmbeddingError as e:
        logger.error(f"Embedding error: {e}")
        if e.original_error:
            logger.error(f"Original error: {e.original_error}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def setup_environment():
    """Load environment variables from .env file and set defaults if needed."""
    # Load .env file from project root
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        logger.info(f"Loading environment variables from {env_file}")
        load_dotenv(env_file)
    else:
        logger.warning(f"No .env file found at {env_file}")
    
    # Check if required environment variables are set and provide defaults
    if not os.getenv("OLLAMA_BASE_URL"):
        logger.info("OLLAMA_BASE_URL not set, using default: http://localhost:11434")
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
    
    if not os.getenv("OLLAMA_MODEL_NAME"):
        logger.info("OLLAMA_MODEL_NAME not set, using default: nomic-embed-text")
        os.environ["OLLAMA_MODEL_NAME"] = "nomic-embed-text"
    
    # Log the configuration being used
    logger.info(f"Environment configuration:")
    logger.info(f"  OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL')}")
    logger.info(f"  OLLAMA_MODEL_NAME: {os.getenv('OLLAMA_MODEL_NAME')}")
    logger.info(f"  OLLAMA_TIMEOUT: {os.getenv('OLLAMA_TIMEOUT', 'default')}")
    logger.info(f"  OLLAMA_MAX_RETRIES: {os.getenv('OLLAMA_MAX_RETRIES', 'default')}")
    logger.info(f"  OLLAMA_BATCH_SIZE: {os.getenv('OLLAMA_BATCH_SIZE', 'default')}")


if __name__ == "__main__":
    setup_environment()
    asyncio.run(main())