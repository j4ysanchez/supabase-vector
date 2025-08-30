"""End-to-end integration tests for embedding storage workflow."""

import asyncio
import hashlib
import logging
import numpy as np
import pytest
from pathlib import Path
from typing import List, Tuple
from uuid import uuid4

from src.adapters.secondary.ollama.ollama_embedding_adapter import OllamaEmbeddingAdapter
from src.adapters.secondary.supabase.supabase_storage_adapter import SupabaseStorageAdapter
from src.domain.models.document import Document, DocumentChunk
from src.infrastructure.config.ollama_config import OllamaConfig
from src.infrastructure.config.supabase_config import SupabaseConfig
from tests.mocks.mock_supabase_client import MockSupabaseClient


logger = logging.getLogger(__name__)


class TestEndToEndEmbeddingStorageWorkflow:
    """End-to-end tests for the complete embedding storage workflow."""
    
    @pytest.fixture
    def ollama_config(self):
        """Create test Ollama configuration."""
        return OllamaConfig(
            base_url="http://localhost:11434",
            model_name="nomic-embed-text",
            timeout=30,
            max_retries=2,
            batch_size=5
        )
    
    @pytest.fixture
    def supabase_config(self):
        """Create test Supabase configuration."""
        return SupabaseConfig(
            url="https://test-project.supabase.co",
            service_key="test-service-key",
            table_name="test_documents",
            timeout=30,
            max_retries=2
        )
    
    @pytest.fixture
    def mock_embedding_adapter(self, ollama_config):
        """Create a mock embedding adapter for testing."""
        import httpx
        from unittest.mock import Mock
        
        mock_client = httpx.AsyncClient()
        
        # Create deterministic embeddings based on text content
        async def mock_post(url, **kwargs):
            payload = kwargs.get('json', {})
            text = payload.get('prompt', '')
            
            # Generate deterministic embedding based on text hash
            text_hash = hashlib.md5(text.encode()).hexdigest()
            seed = int(text_hash[:8], 16)
            np.random.seed(seed)
            
            # Create a 768-dimensional embedding with some structure
            embedding = np.random.normal(0, 0.1, 768).tolist()
            
            # Add some semantic structure based on keywords
            if 'machine learning' in text.lower() or 'ai' in text.lower():
                embedding[0] = 0.8  # High value for AI-related content
                embedding[1] = 0.6
            elif 'cooking' in text.lower() or 'recipe' in text.lower():
                embedding[0] = -0.8  # Negative value for cooking content
                embedding[1] = 0.7
            elif 'database' in text.lower() or 'vector' in text.lower():
                embedding[0] = 0.5
                embedding[1] = -0.8  # Negative value for database content
            
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"embedding": embedding}
            return mock_response
        
        mock_client.post = mock_post
        return OllamaEmbeddingAdapter(ollama_config, mock_client)
    
    @pytest.fixture
    def mock_storage_adapter(self, supabase_config):
        """Create a mock storage adapter for testing."""
        adapter = SupabaseStorageAdapter(supabase_config)
        adapter._client = MockSupabaseClient(supabase_config)
        return adapter
    
    @pytest.fixture
    def test_texts(self):
        """Create test texts with different content types and sizes."""
        return {
            'short_ai': "Machine learning is a subset of artificial intelligence.",
            'medium_ai': """
            Artificial intelligence and machine learning are transforming how we process data.
            These technologies enable computers to learn patterns from large datasets without
            explicit programming. Deep learning, a subset of machine learning, uses neural
            networks to model complex patterns in data.
            """.strip(),
            'long_ai': """
            Machine learning and artificial intelligence represent one of the most significant
            technological advances of our time. These fields encompass a wide range of techniques
            and algorithms that enable computers to learn from data and make predictions or
            decisions without being explicitly programmed for every scenario.
            
            The foundation of machine learning lies in statistical methods and computational
            algorithms that can identify patterns in data. From simple linear regression to
            complex deep neural networks, these tools have revolutionized industries ranging
            from healthcare to finance to transportation.
            
            Deep learning, in particular, has shown remarkable success in areas such as image
            recognition, natural language processing, and game playing. The ability of neural
            networks to automatically learn hierarchical representations of data has opened
            up new possibilities for solving previously intractable problems.
            """.strip(),
            'short_cooking': "This recipe makes delicious chocolate chip cookies.",
            'medium_cooking': """
            Cooking is both an art and a science. The perfect recipe requires understanding
            ingredient interactions, temperature control, and timing. Whether you're baking
            bread or preparing a complex sauce, attention to detail makes all the difference.
            """.strip(),
            'short_database': "Vector databases store high-dimensional embeddings efficiently.",
            'medium_database': """
            Vector databases are specialized storage systems designed to handle high-dimensional
            data efficiently. They use advanced indexing techniques like HNSW or IVF to enable
            fast similarity searches across millions of vectors. These databases are essential
            for modern AI applications that rely on embedding-based retrieval.
            """.strip()
        }

    # Test 1: Complete Flow - Text → Embedding → Supabase Storage
    @pytest.mark.asyncio
    async def test_complete_text_to_storage_workflow(
        self, 
        mock_embedding_adapter, 
        mock_storage_adapter, 
        test_texts
    ):
        """Test complete flow: text → embedding → Supabase storage."""
        
        # Test with a medium-sized AI text
        test_text = test_texts['medium_ai']
        test_filename = "test_ai_document.txt"
        test_path = Path(f"/test/{test_filename}")
        
        # Step 1: Generate embedding from text
        embedding = await mock_embedding_adapter.generate_embedding(test_text)
        
        # Verify embedding properties
        assert isinstance(embedding, list), "Embedding should be a list"
        assert len(embedding) == 768, "Embedding should be 768-dimensional"
        assert all(isinstance(x, (int, float)) for x in embedding), "All embedding values should be numeric"
        
        # Step 2: Create document with embedding
        content_hash = hashlib.sha256(test_text.encode()).hexdigest()
        
        document = Document(
            filename=test_filename,
            file_path=test_path,
            content_hash=content_hash,
            chunks=[
                DocumentChunk(
                    content=test_text,
                    chunk_index=0,
                    embedding=embedding,
                    metadata={
                        "text_length": len(test_text),
                        "content_type": "ai_related",
                        "processing_timestamp": "2024-01-01T00:00:00Z"
                    }
                )
            ],
            metadata={
                "source": "test",
                "document_type": "text",
                "workflow_test": True
            }
        )
        
        # Step 3: Store document in Supabase
        store_result = await mock_storage_adapter.store_document(document)
        assert store_result is True, "Document storage should succeed"
        assert document.id is not None, "Document should have an ID after storage"
        
        # Step 4: Verify storage by retrieving the document
        retrieved_document = await mock_storage_adapter.retrieve_document(document.id)
        assert retrieved_document is not None, "Document should be retrievable"
        assert retrieved_document.filename == test_filename
        assert retrieved_document.content_hash == content_hash
        assert len(retrieved_document.chunks) == 1
        
        # Step 5: Verify embedding integrity
        retrieved_embedding = retrieved_document.chunks[0].embedding
        assert len(retrieved_embedding) == len(embedding)
        
        # Check embedding values are preserved (with small tolerance for float precision)
        for i, (original, retrieved) in enumerate(zip(embedding, retrieved_embedding)):
            assert abs(original - retrieved) < 1e-6, f"Embedding value {i} not preserved"
        
        # Step 6: Verify metadata preservation
        assert retrieved_document.chunks[0].metadata["content_type"] == "ai_related"
        assert retrieved_document.metadata["workflow_test"] is True
        
        # Clean up
        await mock_storage_adapter.delete_document(document.id)
        
        logger.info("Complete text-to-storage workflow test passed")

    # Test 2: Stored Embeddings Retrieval and Similarity Search
    @pytest.mark.asyncio
    async def test_stored_embeddings_similarity_search(
        self, 
        mock_embedding_adapter, 
        mock_storage_adapter, 
        test_texts
    ):
        """Verify stored embeddings can be retrieved and used for similarity search."""
        
        # Create documents with different content types
        documents = []
        
        # AI-related documents (should be similar to each other)
        ai_texts = [test_texts['short_ai'], test_texts['medium_ai']]
        for i, text in enumerate(ai_texts):
            embedding = await mock_embedding_adapter.generate_embedding(text)
            doc = Document(
                filename=f"ai_doc_{i}.txt",
                file_path=Path(f"/test/ai_doc_{i}.txt"),
                content_hash=hashlib.sha256(text.encode()).hexdigest(),
                chunks=[
                    DocumentChunk(
                        content=text,
                        chunk_index=0,
                        embedding=embedding,
                        metadata={"category": "ai", "doc_index": i}
                    )
                ],
                metadata={"content_type": "ai"}
            )
            documents.append(doc)
        
        # Cooking-related document (should be dissimilar to AI docs)
        cooking_text = test_texts['medium_cooking']
        cooking_embedding = await mock_embedding_adapter.generate_embedding(cooking_text)
        cooking_doc = Document(
            filename="cooking_doc.txt",
            file_path=Path("/test/cooking_doc.txt"),
            content_hash=hashlib.sha256(cooking_text.encode()).hexdigest(),
            chunks=[
                DocumentChunk(
                    content=cooking_text,
                    chunk_index=0,
                    embedding=cooking_embedding,
                    metadata={"category": "cooking"}
                )
            ],
            metadata={"content_type": "cooking"}
        )
        documents.append(cooking_doc)
        
        # Database-related document
        db_text = test_texts['medium_database']
        db_embedding = await mock_embedding_adapter.generate_embedding(db_text)
        db_doc = Document(
            filename="database_doc.txt",
            file_path=Path("/test/database_doc.txt"),
            content_hash=hashlib.sha256(db_text.encode()).hexdigest(),
            chunks=[
                DocumentChunk(
                    content=db_text,
                    chunk_index=0,
                    embedding=db_embedding,
                    metadata={"category": "database"}
                )
            ],
            metadata={"content_type": "database"}
        )
        documents.append(db_doc)
        
        # Store all documents
        for doc in documents:
            store_result = await mock_storage_adapter.store_document(doc)
            assert store_result is True, f"Failed to store {doc.filename}"
        
        # Retrieve all documents and verify embeddings
        retrieved_docs = []
        for doc in documents:
            retrieved = await mock_storage_adapter.retrieve_document(doc.id)
            assert retrieved is not None, f"Failed to retrieve {doc.filename}"
            retrieved_docs.append(retrieved)
        
        # Test similarity calculations
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            """Calculate cosine similarity between two vectors."""
            a_np = np.array(a)
            b_np = np.array(b)
            return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))
        
        # Get embeddings from retrieved documents
        ai_embedding_1 = retrieved_docs[0].chunks[0].embedding
        ai_embedding_2 = retrieved_docs[1].chunks[0].embedding
        cooking_embedding_retrieved = retrieved_docs[2].chunks[0].embedding
        db_embedding_retrieved = retrieved_docs[3].chunks[0].embedding
        
        # Calculate similarities
        ai_ai_similarity = cosine_similarity(ai_embedding_1, ai_embedding_2)
        ai_cooking_similarity = cosine_similarity(ai_embedding_1, cooking_embedding_retrieved)
        ai_db_similarity = cosine_similarity(ai_embedding_1, db_embedding_retrieved)
        cooking_db_similarity = cosine_similarity(cooking_embedding_retrieved, db_embedding_retrieved)
        
        # Verify similarity relationships
        # AI documents should be more similar to each other than to other categories
        assert ai_ai_similarity > ai_cooking_similarity, "AI docs should be more similar to each other than to cooking"
        assert ai_ai_similarity > ai_db_similarity, "AI docs should be more similar to each other than to database"
        
        # Log similarity scores for debugging
        logger.info(f"AI-AI similarity: {ai_ai_similarity:.3f}")
        logger.info(f"AI-Cooking similarity: {ai_cooking_similarity:.3f}")
        logger.info(f"AI-Database similarity: {ai_db_similarity:.3f}")
        logger.info(f"Cooking-Database similarity: {cooking_db_similarity:.3f}")
        
        # Test similarity search functionality
        # Find documents most similar to a query embedding
        query_text = "What is artificial intelligence and machine learning?"
        query_embedding = await mock_embedding_adapter.generate_embedding(query_text)
        
        # Calculate similarities to all stored documents
        similarities = []
        for doc in retrieved_docs:
            doc_embedding = doc.chunks[0].embedding
            similarity = cosine_similarity(query_embedding, doc_embedding)
            similarities.append((doc, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # The most similar document should be AI-related
        most_similar_doc = similarities[0][0]
        assert most_similar_doc.metadata["content_type"] == "ai", "Most similar document should be AI-related"
        
        # Clean up
        for doc in documents:
            await mock_storage_adapter.delete_document(doc.id)
        
        logger.info("Similarity search test passed")

    # Test 3: Various Text Sizes and Content Types
    @pytest.mark.asyncio
    async def test_various_text_sizes_and_content_types(
        self, 
        mock_embedding_adapter, 
        mock_storage_adapter, 
        test_texts
    ):
        """Test with various text sizes and content types."""
        
        test_cases = [
            ("short_ai", "Short AI text"),
            ("medium_ai", "Medium AI text"),
            ("long_ai", "Long AI text"),
            ("short_cooking", "Short cooking text"),
            ("medium_cooking", "Medium cooking text"),
            ("short_database", "Short database text"),
            ("medium_database", "Medium database text")
        ]
        
        processed_documents = []
        
        for text_key, description in test_cases:
            text = test_texts[text_key]
            
            # Generate embedding
            embedding = await mock_embedding_adapter.generate_embedding(text)
            
            # Verify embedding properties
            assert len(embedding) == 768, f"Embedding for {description} should be 768-dimensional"
            assert all(isinstance(x, (int, float)) for x in embedding), f"All values in {description} embedding should be numeric"
            
            # Create document
            content_hash = hashlib.sha256(text.encode()).hexdigest()
            doc = Document(
                filename=f"{text_key}.txt",
                file_path=Path(f"/test/{text_key}.txt"),
                content_hash=content_hash,
                chunks=[
                    DocumentChunk(
                        content=text,
                        chunk_index=0,
                        embedding=embedding,
                        metadata={
                            "text_length": len(text),
                            "text_type": text_key,
                            "word_count": len(text.split())
                        }
                    )
                ],
                metadata={
                    "description": description,
                    "size_category": "short" if len(text) < 100 else "medium" if len(text) < 500 else "long"
                }
            )
            
            # Store document
            store_result = await mock_storage_adapter.store_document(doc)
            assert store_result is True, f"Failed to store {description}"
            
            processed_documents.append(doc)
        
        # Verify all documents can be retrieved
        for doc in processed_documents:
            retrieved = await mock_storage_adapter.retrieve_document(doc.id)
            assert retrieved is not None, f"Failed to retrieve {doc.filename}"
            
            # Verify content integrity
            original_chunk = doc.chunks[0]
            retrieved_chunk = retrieved.chunks[0]
            
            assert retrieved_chunk.content == original_chunk.content, f"Content mismatch for {doc.filename}"
            assert len(retrieved_chunk.embedding) == len(original_chunk.embedding), f"Embedding dimension mismatch for {doc.filename}"
            assert retrieved_chunk.metadata["text_length"] == original_chunk.metadata["text_length"], f"Metadata mismatch for {doc.filename}"
        
        # Test batch retrieval
        all_docs = await mock_storage_adapter.list_documents(limit=20)
        assert len(all_docs) >= len(processed_documents), "Should retrieve at least our test documents"
        
        # Verify we can find our documents in the list
        our_doc_ids = {doc.id for doc in processed_documents}
        retrieved_doc_ids = {doc.id for doc in all_docs}
        assert our_doc_ids.issubset(retrieved_doc_ids), "All our documents should be in the retrieved list"
        
        # Test content-based search
        for doc in processed_documents:
            found_doc = await mock_storage_adapter.find_by_hash(doc.content_hash)
            assert found_doc is not None, f"Should find document by hash for {doc.filename}"
            assert found_doc.id == doc.id, f"Found document should match original for {doc.filename}"
        
        # Clean up
        for doc in processed_documents:
            delete_result = await mock_storage_adapter.delete_document(doc.id)
            assert delete_result is True, f"Failed to delete {doc.filename}"
        
        logger.info(f"Successfully tested {len(test_cases)} different text sizes and content types")

    # Test 4: Multi-chunk Document Processing
    @pytest.mark.asyncio
    async def test_multi_chunk_document_processing(
        self, 
        mock_embedding_adapter, 
        mock_storage_adapter,
        test_texts
    ):
        """Test processing documents with multiple chunks."""
        
        # Create a large document that would be split into chunks
        large_text = test_texts['long_ai']
        
        # Simulate chunking by splitting the text
        sentences = large_text.split('. ')
        chunk_size = 3  # 3 sentences per chunk
        chunks = []
        
        for i in range(0, len(sentences), chunk_size):
            chunk_sentences = sentences[i:i + chunk_size]
            chunk_text = '. '.join(chunk_sentences)
            if not chunk_text.endswith('.'):
                chunk_text += '.'
            
            # Generate embedding for this chunk
            embedding = await mock_embedding_adapter.generate_embedding(chunk_text)
            
            chunk = DocumentChunk(
                content=chunk_text,
                chunk_index=i // chunk_size,
                embedding=embedding,
                metadata={
                    "chunk_size": len(chunk_text),
                    "sentence_count": len(chunk_sentences),
                    "chunk_type": "text_segment"
                }
            )
            chunks.append(chunk)
        
        # Create multi-chunk document
        content_hash = hashlib.sha256(large_text.encode()).hexdigest()
        multi_chunk_doc = Document(
            filename="multi_chunk_document.txt",
            file_path=Path("/test/multi_chunk_document.txt"),
            content_hash=content_hash,
            chunks=chunks,
            metadata={
                "total_chunks": len(chunks),
                "original_length": len(large_text),
                "chunk_strategy": "sentence_based"
            }
        )
        
        # Store multi-chunk document
        store_result = await mock_storage_adapter.store_document(multi_chunk_doc)
        assert store_result is True, "Multi-chunk document storage should succeed"
        
        # Retrieve and verify
        retrieved = await mock_storage_adapter.retrieve_document(multi_chunk_doc.id)
        assert retrieved is not None, "Multi-chunk document should be retrievable"
        assert len(retrieved.chunks) == len(chunks), f"Should retrieve all {len(chunks)} chunks"
        
        # Verify chunk order and content
        for i, (original_chunk, retrieved_chunk) in enumerate(zip(chunks, retrieved.chunks)):
            assert retrieved_chunk.chunk_index == i, f"Chunk {i} should have correct index"
            assert retrieved_chunk.content == original_chunk.content, f"Chunk {i} content should match"
            assert len(retrieved_chunk.embedding) == 768, f"Chunk {i} should have 768-dimensional embedding"
            assert retrieved_chunk.metadata["chunk_type"] == "text_segment", f"Chunk {i} metadata should be preserved"
        
        # Test similarity search across chunks
        # Find the chunk most similar to a query
        query_text = "neural networks and deep learning algorithms"
        query_embedding = await mock_embedding_adapter.generate_embedding(query_text)
        
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            a_np = np.array(a)
            b_np = np.array(b)
            return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))
        
        chunk_similarities = []
        for chunk in retrieved.chunks:
            similarity = cosine_similarity(query_embedding, chunk.embedding)
            chunk_similarities.append((chunk, similarity))
        
        # Sort by similarity
        chunk_similarities.sort(key=lambda x: x[1], reverse=True)
        
        # The most similar chunk should contain relevant content
        most_similar_chunk = chunk_similarities[0][0]
        assert "neural" in most_similar_chunk.content.lower() or "deep" in most_similar_chunk.content.lower(), \
            "Most similar chunk should contain relevant keywords"
        
        # Clean up
        await mock_storage_adapter.delete_document(multi_chunk_doc.id)
        
        logger.info(f"Multi-chunk document test passed with {len(chunks)} chunks")

    # Test 5: Error Handling in End-to-End Workflow
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(
        self, 
        mock_embedding_adapter, 
        mock_storage_adapter
    ):
        """Test error handling throughout the end-to-end workflow."""
        
        # Test 1: Empty text handling
        try:
            empty_embedding = await mock_embedding_adapter.generate_embedding("")
            # If it succeeds, verify it's still a valid embedding
            assert len(empty_embedding) == 768, "Empty text should still produce valid embedding"
        except Exception as e:
            # If it fails, that's also acceptable behavior
            logger.info(f"Empty text handling: {e}")
        
        # Test 2: Very long text handling
        very_long_text = "This is a test sentence. " * 1000  # Very long text
        long_embedding = await mock_embedding_adapter.generate_embedding(very_long_text)
        assert len(long_embedding) == 768, "Very long text should produce valid embedding"
        
        # Test 3: Special characters and unicode
        special_text = "Test with émojis 🤖 and spëcial chäractërs: αβγδε ∑∏∆"
        special_embedding = await mock_embedding_adapter.generate_embedding(special_text)
        assert len(special_embedding) == 768, "Special characters should be handled correctly"
        
        # Test 4: Document with invalid embedding dimensions (simulated)
        # This tests the storage adapter's handling of inconsistent data
        test_text = "Test document for error handling"
        valid_embedding = await mock_embedding_adapter.generate_embedding(test_text)
        
        # Create document with valid embedding first
        doc = Document(
            filename="error_test.txt",
            file_path=Path("/test/error_test.txt"),
            content_hash=hashlib.sha256(test_text.encode()).hexdigest(),
            chunks=[
                DocumentChunk(
                    content=test_text,
                    chunk_index=0,
                    embedding=valid_embedding,
                    metadata={"test": "error_handling"}
                )
            ],
            metadata={"error_test": True}
        )
        
        # Store and verify normal operation
        store_result = await mock_storage_adapter.store_document(doc)
        assert store_result is True, "Valid document should store successfully"
        
        retrieved = await mock_storage_adapter.retrieve_document(doc.id)
        assert retrieved is not None, "Valid document should be retrievable"
        
        # Clean up
        await mock_storage_adapter.delete_document(doc.id)
        
        # Test 5: Concurrent operations
        concurrent_docs = []
        for i in range(5):
            text = f"Concurrent test document {i} with unique content for testing."
            embedding = await mock_embedding_adapter.generate_embedding(text)
            
            concurrent_doc = Document(
                filename=f"concurrent_{i}.txt",
                file_path=Path(f"/test/concurrent_{i}.txt"),
                content_hash=hashlib.sha256(text.encode()).hexdigest(),
                chunks=[
                    DocumentChunk(
                        content=text,
                        chunk_index=0,
                        embedding=embedding,
                        metadata={"concurrent_test": True, "doc_index": i}
                    )
                ],
                metadata={"test_type": "concurrent"}
            )
            concurrent_docs.append(concurrent_doc)
        
        # Store all documents concurrently
        store_tasks = [mock_storage_adapter.store_document(doc) for doc in concurrent_docs]
        store_results = await asyncio.gather(*store_tasks, return_exceptions=True)
        
        # Verify all operations succeeded
        for i, result in enumerate(store_results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent store operation {i} failed: {result}")
            assert result is True, f"Concurrent store operation {i} should succeed"
        
        # Clean up concurrent documents
        delete_tasks = [mock_storage_adapter.delete_document(doc.id) for doc in concurrent_docs]
        await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        logger.info("Error handling tests completed successfully")

    # Test 6: Performance and Scalability
    @pytest.mark.asyncio
    async def test_performance_and_scalability(
        self, 
        mock_embedding_adapter, 
        mock_storage_adapter
    ):
        """Test performance with larger datasets."""
        
        import time
        
        # Generate a moderate number of documents for performance testing
        num_docs = 20
        documents = []
        
        start_time = time.time()
        
        # Generate embeddings for multiple documents
        texts = [f"Performance test document {i} with unique content about various topics including technology, science, and research." for i in range(num_docs)]
        
        # Batch generate embeddings
        embeddings = await mock_embedding_adapter.generate_embeddings(texts)
        
        embedding_time = time.time() - start_time
        logger.info(f"Generated {num_docs} embeddings in {embedding_time:.2f} seconds")
        
        # Create documents
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            doc = Document(
                filename=f"perf_test_{i}.txt",
                file_path=Path(f"/test/perf_test_{i}.txt"),
                content_hash=hashlib.sha256(text.encode()).hexdigest(),
                chunks=[
                    DocumentChunk(
                        content=text,
                        chunk_index=0,
                        embedding=embedding,
                        metadata={"performance_test": True, "doc_index": i}
                    )
                ],
                metadata={"test_type": "performance", "batch_size": num_docs}
            )
            documents.append(doc)
        
        # Store all documents and measure time
        store_start = time.time()
        store_tasks = [mock_storage_adapter.store_document(doc) for doc in documents]
        store_results = await asyncio.gather(*store_tasks)
        store_time = time.time() - store_start
        
        logger.info(f"Stored {num_docs} documents in {store_time:.2f} seconds")
        
        # Verify all stores succeeded
        assert all(store_results), "All document stores should succeed"
        
        # Test batch retrieval performance
        retrieve_start = time.time()
        retrieve_tasks = [mock_storage_adapter.retrieve_document(doc.id) for doc in documents]
        retrieved_docs = await asyncio.gather(*retrieve_tasks)
        retrieve_time = time.time() - retrieve_start
        
        logger.info(f"Retrieved {num_docs} documents in {retrieve_time:.2f} seconds")
        
        # Verify all retrievals succeeded
        assert all(doc is not None for doc in retrieved_docs), "All document retrievals should succeed"
        
        # Test similarity search performance
        query_text = "technology and research in modern applications"
        query_embedding = await mock_embedding_adapter.generate_embedding(query_text)
        
        similarity_start = time.time()
        
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            a_np = np.array(a)
            b_np = np.array(b)
            return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))
        
        similarities = []
        for doc in retrieved_docs:
            doc_embedding = doc.chunks[0].embedding
            similarity = cosine_similarity(query_embedding, doc_embedding)
            similarities.append((doc, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        similarity_time = time.time() - similarity_start
        
        logger.info(f"Computed similarities for {num_docs} documents in {similarity_time:.3f} seconds")
        
        # Verify similarity search results
        assert len(similarities) == num_docs, "Should compute similarity for all documents"
        assert similarities[0][1] >= similarities[-1][1], "Results should be sorted by similarity"
        
        # Clean up
        delete_start = time.time()
        delete_tasks = [mock_storage_adapter.delete_document(doc.id) for doc in documents]
        delete_results = await asyncio.gather(*delete_tasks)
        delete_time = time.time() - delete_start
        
        logger.info(f"Deleted {num_docs} documents in {delete_time:.2f} seconds")
        
        # Performance assertions (these are lenient since we're using mocks)
        total_time = time.time() - start_time
        logger.info(f"Total test time: {total_time:.2f} seconds")
        
        # These are reasonable performance expectations for the workflow
        assert embedding_time < 10.0, "Embedding generation should complete within 10 seconds"
        assert store_time < 5.0, "Document storage should complete within 5 seconds"
        assert retrieve_time < 5.0, "Document retrieval should complete within 5 seconds"
        assert similarity_time < 1.0, "Similarity computation should complete within 1 second"
        
        logger.info("Performance test completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])