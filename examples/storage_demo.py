"""Demonstration of StoragePort interface and Supabase adapter usage."""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adapters.secondary.supabase import SupabaseStorageAdapter
from src.domain.models import Document, DocumentChunk
from src.config import get_supabase_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demonstrate_storage_operations():
    """Demonstrate basic storage operations using the StoragePort interface."""
    
    logger.info("=== Storage Port Demonstration ===")
    
    # 1. Create configuration
    logger.info("1. Creating Supabase configuration...")
    config = get_supabase_config()
    
    
    # 2. Create storage adapter
    logger.info("2. Initializing Supabase storage adapter...")
    storage: SupabaseStorageAdapter = SupabaseStorageAdapter(config)
    
    # 3. Health check
    logger.info("3. Performing health check...")
    is_healthy = await storage.health_check()
    logger.info(f"   Storage health: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
    
    if not is_healthy:
        logger.error("Storage is not healthy. Exiting demonstration.")
        return
    
    # 4. Create sample documents
    logger.info("4. Creating sample documents...")
    
    # Document 1: Simple text document
    # Create 768-dimensional embeddings (matching Supabase schema)
    embedding1 = [0.1] * 768  # Simple mock embedding with 768 dimensions
    embedding2 = [0.2] * 768  # Another mock embedding with 768 dimensions
    
    doc1_chunks = [
        DocumentChunk(
            content="Introduction to vector databases and their applications in modern AI systems.",
            chunk_index=0,
            embedding=embedding1,
            metadata={"section": "introduction", "word_count": 12}
        ),
        DocumentChunk(
            content="Vector databases enable efficient similarity search and retrieval of high-dimensional data.",
            chunk_index=1,
            embedding=embedding2,
            metadata={"section": "overview", "word_count": 13}
        )
    ]
    
    document1 = Document(
        filename="vector_db_intro.txt",
        file_path=Path("/documents/vector_db_intro.txt"),
        content_hash="hash_doc1_abc123",
        chunks=doc1_chunks,
        metadata={
            "author": "AI Researcher",
            "topic": "vector_databases",
            "language": "english",
            "created_date": "2024-01-15"
        }
    )
    
    # Document 2: Technical documentation
    embedding3 = [0.3] * 768  # Third mock embedding with 768 dimensions
    
    doc2_chunks = [
        DocumentChunk(
            content="Implementation details for embedding generation using transformer models.",
            chunk_index=0,
            embedding=embedding3,
            metadata={"section": "implementation", "technical_level": "advanced"}
        )
    ]
    
    document2 = Document(
        filename="embedding_implementation.md",
        file_path=Path("/documents/technical/embedding_implementation.md"),
        content_hash="hash_doc2_def456",
        chunks=doc2_chunks,
        metadata={
            "author": "Technical Writer",
            "topic": "embeddings",
            "format": "markdown",
            "created_date": "2024-01-16"
        }
    )
    
    # 5. Store documents
    logger.info("5. Storing documents...")
    
    logger.info(f"   Storing document: {document1.filename}")
    result1 = await storage.store_document(document1)
    logger.info(f"   Result: {'✓ Success' if result1 else '✗ Failed'}")
    
    logger.info(f"   Storing document: {document2.filename}")
    result2 = await storage.store_document(document2)
    logger.info(f"   Result: {'✓ Success' if result2 else '✗ Failed'}")
    
    if not (result1 and result2):
        logger.error("Failed to store documents. Exiting demonstration.")
        return
    
    # 6. Retrieve documents
    logger.info("6. Retrieving documents...")
    
    logger.info(f"   Retrieving document by ID: {document1.id}")
    retrieved1 = await storage.retrieve_document(document1.id)
    if retrieved1:
        logger.info(f"   ✓ Retrieved: {retrieved1.filename} ({len(retrieved1.chunks)} chunks)")
    else:
        logger.warning("   ✗ Document not found")
    
    # 7. Search by content hash
    logger.info("7. Searching by content hash...")
    
    logger.info(f"   Searching for hash: {document2.content_hash}")
    found_doc = await storage.find_by_hash(document2.content_hash)
    if found_doc:
        logger.info(f"   ✓ Found: {found_doc.filename}")
    else:
        logger.warning("   ✗ Document not found by hash")
    
    # 8. List all documents
    logger.info("8. Listing all documents...")
    
    all_documents = await storage.list_documents(limit=10)
    logger.info(f"   Found {len(all_documents)} documents:")
    for i, doc in enumerate(all_documents, 1):
        logger.info(f"     {i}. {doc.filename} ({len(doc.chunks)} chunks)")
    
    # 9. Demonstrate error handling
    logger.info("9. Demonstrating error handling...")
    
    # Try to retrieve non-existent document
    from uuid import uuid4
    fake_id = uuid4()
    logger.info(f"   Attempting to retrieve non-existent document: {fake_id}")
    non_existent = await storage.retrieve_document(fake_id)
    logger.info(f"   Result: {'Found' if non_existent else '✓ Correctly returned None'}")
    
    # Try to find by non-existent hash
    logger.info("   Searching for non-existent hash: 'fake_hash_xyz'")
    not_found = await storage.find_by_hash("fake_hash_xyz")
    logger.info(f"   Result: {'Found' if not_found else '✓ Correctly returned None'}")
    
    # 10. Clean up (delete documents)
    logger.info("10. Cleaning up (deleting test documents)...")
    
    logger.info(f"    Deleting document: {document1.id}")
    delete1 = await storage.delete_document(document1.id)
    logger.info(f"    Result: {'✓ Deleted' if delete1 else '✗ Failed'}")
    
    logger.info(f"    Deleting document: {document2.id}")
    delete2 = await storage.delete_document(document2.id)
    logger.info(f"    Result: {'✓ Deleted' if delete2 else '✗ Failed'}")
    
    # Verify deletion
    logger.info("    Verifying deletion...")
    verify1 = await storage.retrieve_document(document1.id)
    verify2 = await storage.retrieve_document(document2.id)
    
    if verify1 is None and verify2 is None:
        logger.info("    ✓ All documents successfully deleted")
    else:
        logger.warning("    ✗ Some documents may not have been deleted properly")
    
    logger.info("=== Demonstration Complete ===")


async def demonstrate_error_scenarios():
    """Demonstrate error handling scenarios."""
    
    logger.info("\n=== Error Handling Demonstration ===")
    
    # Create adapter with invalid configuration
    logger.info("1. Testing with invalid configuration...")
    
    try:
        invalid_config = SupabaseConfig(
            url="",  # Invalid empty URL
            service_key="test-key",
            table_name="test_table"
        )
        invalid_config.validate()
        logger.error("   ✗ Validation should have failed")
    except Exception as e:
        logger.info(f"   ✓ Correctly caught configuration error: {e}")
    
    logger.info("=== Error Handling Complete ===")


if __name__ == "__main__":
    async def main():
        await demonstrate_storage_operations()
        await demonstrate_error_scenarios()
    
    asyncio.run(main())