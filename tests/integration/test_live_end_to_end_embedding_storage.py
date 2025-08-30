"""Live end-to-end integration tests for embedding storage workflow.

These tests use real Ollama and Supabase services to test the complete workflow:
text → embedding generation → vector storage → similarity search

IMPORTANT: These tests will:
- Connect to your live Ollama service
- Connect to your live Supabase database
- Create and delete real data
- Use actual embedding generation

Make sure you have:
1. Ollama running with nomic-embed-text model
2. Supabase database with proper schema
3. Environment variables configured
"""

import asyncio
import hashlib
import logging
import numpy as np
import os
import pytest
from pathlib import Path
from typing import List, Tuple
from uuid import uuid4
from datetime import datetime

from src.adapters.secondary.ollama.ollama_embedding_adapter import OllamaEmbeddingAdapter
from src.adapters.secondary.supabase.supabase_storage_adapter import SupabaseStorageAdapter
from src.domain.models.document import Document, DocumentChunk
from src.config import get_ollama_config, get_supabase_config, create_test_ollama_config, create_test_supabase_config
from src.domain.exceptions import EmbeddingError, StorageError


logger = logging.getLogger(__name__)


class LiveSupabaseStorageAdapter(SupabaseStorageAdapter):
    """Live Supabase adapter that uses the real Supabase client."""
    
    async def _get_client(self):
        """Get or create the real Supabase client."""
        if self._client is None:
            try:
                from supabase import create_client, Client
                self._client = create_client(self._config.url, self._config.service_key)
                logger.info(f"Connected to live Supabase: {self._config.url}")
            except ImportError:
                raise ImportError("supabase package not installed. Run: pip install supabase")
            except Exception as e:
                raise StorageError(f"Failed to connect to Supabase: {e}")
        return self._client


@pytest.mark.live
class TestLiveEndToEndEmbeddingStorageWorkflow:
    """Live end-to-end tests for the complete embedding storage workflow using real services."""
    
    @pytest.fixture(scope="class")
    def ollama_config(self):
        """Create live Ollama configuration from environment."""
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model_name = os.getenv("OLLAMA_MODEL_NAME", "nomic-embed-text")
        
        if not base_url:
            pytest.skip("OLLAMA_BASE_URL environment variable required for live tests")
        
        return create_test_ollama_config(
            base_url=base_url,
            model_name=model_name,
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "60")),
            max_retries=int(os.getenv("OLLAMA_MAX_RETRIES", "2")),
            batch_size=int(os.getenv("OLLAMA_BATCH_SIZE", "5"))
        )
    
    @pytest.fixture(scope="class")
    def supabase_config(self):
        """Create live Supabase configuration from environment."""
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not url or not service_key:
            pytest.skip("SUPABASE_URL and SUPABASE_SERVICE_KEY required for live tests")
        
        return create_test_supabase_config(
            url=url,
            service_key=service_key,
            table_name=os.getenv("SUPABASE_TABLE_NAME", "documents"),
            timeout=int(os.getenv("SUPABASE_TIMEOUT", "30")),
            max_retries=int(os.getenv("SUPABASE_MAX_RETRIES", "2"))
        )
    
    @pytest.fixture(scope="class")
    def live_embedding_adapter(self, ollama_config):
        """Create a live embedding adapter."""
        return OllamaEmbeddingAdapter(ollama_config)
    
    @pytest.fixture(scope="class")
    def live_storage_adapter(self, supabase_config):
        """Create a live storage adapter."""
        return LiveSupabaseStorageAdapter(supabase_config)
    
    @pytest.fixture
    def test_texts(self):
        """Create test texts with different content types and sizes."""
        return {
            'short_ai': "Machine learning algorithms process data to find patterns.",
            'medium_ai': """
            Artificial intelligence and machine learning are revolutionizing how we approach
            complex problems. These technologies enable computers to learn from data and make
            intelligent decisions without explicit programming for every scenario. Deep learning
            neural networks can recognize patterns in images, understand natural language, and
            even generate creative content.
            """.strip(),
            'long_ai': """
            The field of artificial intelligence has evolved dramatically over the past decade,
            with machine learning and deep learning techniques achieving unprecedented success
            across diverse domains. From computer vision systems that can identify objects in
            images with superhuman accuracy to natural language processing models that can
            engage in sophisticated conversations, AI technologies are transforming industries
            and reshaping our understanding of what machines can accomplish.
            
            At the heart of these advances are neural networks - computational models inspired
            by the structure and function of biological brains. These networks consist of
            interconnected nodes that process information through weighted connections, learning
            to recognize complex patterns through exposure to large datasets. The training
            process involves adjusting these weights to minimize prediction errors, gradually
            improving the model's ability to make accurate predictions on new, unseen data.
            
            Vector embeddings play a crucial role in modern AI systems, providing a way to
            represent complex data like text, images, and audio as high-dimensional numerical
            vectors. These embeddings capture semantic relationships and enable similarity
            comparisons that power recommendation systems, search engines, and content
            discovery platforms.
            """.strip(),
            'cooking': """
            Cooking is both an art and a science that brings people together through shared
            meals and culinary experiences. The perfect recipe balances flavors, textures,
            and aromas to create memorable dishes. Understanding ingredient interactions,
            temperature control, and timing are essential skills for any aspiring chef.
            """.strip(),
            'database': """
            Vector databases are specialized storage systems designed to efficiently handle
            high-dimensional data and perform similarity searches. They use advanced indexing
            techniques like HNSW (Hierarchical Navigable Small World) or IVF (Inverted File)
            to enable fast approximate nearest neighbor searches across millions of vectors.
            These databases are essential infrastructure for modern AI applications.
            """.strip()
        }

    # Test 1: Complete Live Workflow - Text → Ollama Embedding → Supabase Storage
    @pytest.mark.asyncio
    async def test_complete_live_workflow(
        self, 
        live_embedding_adapter, 
        live_storage_adapter, 
        test_texts
    ):
        """Test complete live workflow: text → Ollama embedding → Supabase storage."""
        
        print(f"\n🧪 Testing Complete Live Workflow")
        print("=" * 50)
        
        # Use medium AI text for this test
        test_text = test_texts['medium_ai']
        test_filename = f"live_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        document = None
        
        try:
            # Test connections first
            print(f"🔄 Testing service connections...")
            
            # Test Ollama connection
            ollama_health = await live_embedding_adapter.health_check()
            if not ollama_health:
                pytest.skip("Ollama service not healthy - check if service is running and model is available")
            print(f"   ✅ Ollama service: Connected")
            
            # Test Supabase connection
            supabase_health = await live_storage_adapter.health_check()
            if not supabase_health:
                pytest.skip("Supabase database not healthy - check connection and schema")
            print(f"   ✅ Supabase database: Connected")
            
            # Step 1: Generate real embedding using Ollama
            print(f"🔄 Step 1: Generating embedding with Ollama...")
            embedding = await live_embedding_adapter.generate_embedding(test_text)
            
            # Verify embedding properties
            assert isinstance(embedding, list), "Embedding should be a list"
            assert len(embedding) == 768, f"Expected 768-dim embedding, got {len(embedding)}"
            assert all(isinstance(x, (int, float)) for x in embedding), "All embedding values should be numeric"
            
            print(f"✅ Generated {len(embedding)}-dimensional embedding")
            print(f"   First 5 values: {embedding[:5]}")
            print(f"   Embedding norm: {np.linalg.norm(embedding):.4f}")
            
            # Step 2: Create document with real embedding
            print(f"🔄 Step 2: Creating document with embedding...")
            content_hash = hashlib.sha256(test_text.encode()).hexdigest()
            
            document = Document(
                filename=test_filename,
                file_path=Path(f"/test/{test_filename}"),
                content_hash=content_hash,
                chunks=[
                    DocumentChunk(
                        content=test_text,
                        chunk_index=0,
                        embedding=embedding,
                        metadata={
                            "text_length": len(test_text),
                            "content_type": "ai_related",
                            "embedding_model": "nomic-embed-text",
                            "test_type": "live_workflow"
                        }
                    )
                ],
                metadata={
                    "source": "live_test",
                    "document_type": "text",
                    "workflow_test": True,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            # Step 3: Store document in live Supabase
            print(f"🔄 Step 3: Storing document in Supabase...")
            store_result = await live_storage_adapter.store_document(document)
            assert store_result is True, "Document storage should succeed"
            assert document.id is not None, "Document should have an ID after storage"
            
            print(f"✅ Stored document with ID: {document.id}")
            
            # Step 4: Retrieve and verify from live database
            print(f"🔄 Step 4: Retrieving document from Supabase...")
            retrieved_document = await live_storage_adapter.retrieve_document(document.id)
            assert retrieved_document is not None, "Document should be retrievable"
            assert retrieved_document.filename == test_filename
            assert retrieved_document.content_hash == content_hash
            assert len(retrieved_document.chunks) == 1
            
            print(f"✅ Retrieved document: {retrieved_document.filename}")
            
            # Step 5: Verify embedding integrity
            print(f"🔄 Step 5: Verifying embedding integrity...")
            retrieved_embedding = retrieved_document.chunks[0].embedding
            
            # Handle potential string storage issue
            if isinstance(retrieved_embedding, str):
                import json
                retrieved_embedding = json.loads(retrieved_embedding)
            
            assert len(retrieved_embedding) == len(embedding), "Embedding dimensions should match"
            
            # Check embedding similarity (should be identical or very close)
            similarity = np.dot(embedding, retrieved_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(retrieved_embedding)
            )
            assert similarity > 0.99, f"Retrieved embedding should be nearly identical (similarity: {similarity:.6f})"
            
            print(f"✅ Embedding integrity verified (similarity: {similarity:.6f})")
            
            # Step 6: Test content integrity
            print(f"🔄 Step 6: Verifying content and metadata...")
            retrieved_chunk = retrieved_document.chunks[0]
            assert retrieved_chunk.content == test_text, "Content should be preserved exactly"
            assert retrieved_chunk.metadata["content_type"] == "ai_related", "Metadata should be preserved"
            assert retrieved_document.metadata["workflow_test"] is True, "Document metadata should be preserved"
            
            print(f"✅ Content and metadata verified")
            
            print(f"\n🎉 Complete Live Workflow Test PASSED!")
            print(f"   ✅ Ollama embedding generation: Working")
            print(f"   ✅ Supabase storage: Working")
            print(f"   ✅ Data integrity: Verified")
            print(f"   ✅ Metadata preservation: Verified")
            
        finally:
            # Clean up - delete the test document
            if document and document.id:
                print(f"🧹 Cleaning up test document...")
                try:
                    delete_result = await live_storage_adapter.delete_document(document.id)
                    if delete_result:
                        print(f"✅ Test document deleted")
                    else:
                        print(f"⚠️  Test document may not have been deleted")
                except Exception as e:
                    print(f"⚠️  Cleanup error: {e}")

    # Test 2: Live Similarity Search with Real Embeddings
    @pytest.mark.asyncio
    async def test_live_similarity_search(
        self, 
        live_embedding_adapter, 
        live_storage_adapter, 
        test_texts
    ):
        """Test similarity search using real embeddings from Ollama."""
        
        print(f"\n🧪 Testing Live Similarity Search")
        print("=" * 50)
        
        documents = []
        
        try:
            # Test connections first
            print(f"🔄 Testing service connections...")
            
            # Test Ollama connection
            ollama_health = await live_embedding_adapter.health_check()
            if not ollama_health:
                pytest.skip("Ollama service not healthy")
            print(f"   ✅ Ollama service: Connected")
            
            # Test Supabase connection
            supabase_health = await live_storage_adapter.health_check()
            if not supabase_health:
                pytest.skip("Supabase database not healthy")
            print(f"   ✅ Supabase database: Connected")
            
            # Create documents with different content types
            content_types = [
                ('ai_doc_1', test_texts['short_ai'], 'ai'),
                ('ai_doc_2', test_texts['medium_ai'], 'ai'),
                ('cooking_doc', test_texts['cooking'], 'cooking'),
                ('database_doc', test_texts['database'], 'database')
            ]
            
            print(f"🔄 Step 1: Generating embeddings for {len(content_types)} documents...")
            
            for doc_name, text, category in content_types:
                # Generate real embedding
                embedding = await live_embedding_adapter.generate_embedding(text)
                
                # Create document
                doc = Document(
                    filename=f"{doc_name}_{datetime.now().strftime('%H%M%S')}.txt",
                    file_path=Path(f"/test/{doc_name}.txt"),
                    content_hash=hashlib.sha256(text.encode()).hexdigest(),
                    chunks=[
                        DocumentChunk(
                            content=text,
                            chunk_index=0,
                            embedding=embedding,
                            metadata={
                                "category": category,
                                "test_type": "similarity_search"
                            }
                        )
                    ],
                    metadata={
                        "content_type": category,
                        "test_purpose": "similarity_search"
                    }
                )
                documents.append(doc)
                
                print(f"   ✅ Generated embedding for {category} document ({len(embedding)} dims)")
            
            # Store all documents
            print(f"🔄 Step 2: Storing documents in Supabase...")
            for doc in documents:
                store_result = await live_storage_adapter.store_document(doc)
                assert store_result is True, f"Failed to store {doc.filename}"
                print(f"   ✅ Stored {doc.filename}")
            
            # Test similarity search with AI query
            print(f"🔄 Step 3: Testing similarity search...")
            query_text = "What are neural networks and deep learning algorithms?"
            query_embedding = await live_embedding_adapter.generate_embedding(query_text)
            
            print(f"   Query: {query_text}")
            print(f"   Query embedding: {len(query_embedding)} dimensions")
            
            # Retrieve all documents and calculate similarities
            similarities = []
            for doc in documents:
                retrieved = await live_storage_adapter.retrieve_document(doc.id)
                assert retrieved is not None, f"Failed to retrieve {doc.filename}"
                
                doc_embedding = retrieved.chunks[0].embedding
                if isinstance(doc_embedding, str):
                    import json
                    doc_embedding = json.loads(doc_embedding)
                
                # Calculate cosine similarity
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )
                
                similarities.append((retrieved, similarity))
                print(f"   Similarity with {retrieved.metadata['content_type']}: {similarity:.4f}")
            
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            print(f"🔄 Step 4: Verifying similarity rankings...")
            
            # The most similar documents should be AI-related
            most_similar = similarities[0][0]
            second_similar = similarities[1][0]
            
            print(f"   Most similar: {most_similar.metadata['content_type']} (similarity: {similarities[0][1]:.4f})")
            print(f"   Second most: {second_similar.metadata['content_type']} (similarity: {similarities[1][1]:.4f})")
            
            # Verify that AI documents are more similar to AI query than other categories
            ai_similarities = [sim for doc, sim in similarities if doc.metadata['content_type'] == 'ai']
            non_ai_similarities = [sim for doc, sim in similarities if doc.metadata['content_type'] != 'ai']
            
            if ai_similarities and non_ai_similarities:
                max_ai_sim = max(ai_similarities)
                max_non_ai_sim = max(non_ai_similarities)
                
                assert max_ai_sim > max_non_ai_sim, f"AI documents should be more similar to AI query (AI: {max_ai_sim:.4f}, Non-AI: {max_non_ai_sim:.4f})"
                print(f"   ✅ AI documents ranked higher than non-AI documents")
            
            # Test with Supabase similarity search function (if available)
            print(f"🔄 Step 5: Testing Supabase similarity search function...")
            try:
                from supabase import create_client
                client = create_client(
                    live_storage_adapter._config.url,
                    live_storage_adapter._config.service_key
                )
                
                result = client.rpc('similarity_search', {
                    'query_embedding': query_embedding,
                    'similarity_threshold': 0.1,
                    'max_results': 10
                }).execute()
                
                if result.data:
                    print(f"   ✅ Supabase similarity search found {len(result.data)} results:")
                    for i, item in enumerate(result.data[:3]):  # Show top 3
                        print(f"      {i+1}. {item.get('filename', 'N/A')} (similarity: {item.get('similarity', 'N/A'):.4f})")
                else:
                    print(f"   ⚠️  Supabase similarity search returned no results")
                    
            except Exception as e:
                print(f"   ⚠️  Supabase similarity search not available: {e}")
            
            print(f"\n🎉 Live Similarity Search Test PASSED!")
            print(f"   ✅ Real embeddings generated: {len(documents)} documents")
            print(f"   ✅ Similarity calculations: Working")
            print(f"   ✅ Semantic ranking: Verified")
            
        finally:
            # Clean up all test documents
            print(f"🧹 Cleaning up test documents...")
            for doc in documents:
                if doc.id:
                    try:
                        await live_storage_adapter.delete_document(doc.id)
                        print(f"   ✅ Deleted {doc.filename}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to delete {doc.filename}: {e}")

    # Test 3: Live Multi-chunk Document Processing
    @pytest.mark.asyncio
    async def test_live_multi_chunk_processing(
        self, 
        live_embedding_adapter, 
        live_storage_adapter, 
        test_texts
    ):
        """Test processing multi-chunk documents with real embeddings."""
        
        print(f"\n🧪 Testing Live Multi-chunk Document Processing")
        print("=" * 50)
        
        # Use the long AI text and split it into chunks
        long_text = test_texts['long_ai']
        
        # Split into sentences and group into chunks
        sentences = [s.strip() + '.' for s in long_text.split('.') if s.strip()]
        chunk_size = 3  # 3 sentences per chunk
        
        chunks = []
        multi_chunk_doc = None
        
        try:
            # Test connections first
            print(f"🔄 Testing service connections...")
            
            # Test Ollama connection
            ollama_health = await live_embedding_adapter.health_check()
            if not ollama_health:
                pytest.skip("Ollama service not healthy")
            print(f"   ✅ Ollama service: Connected")
            
            # Test Supabase connection
            supabase_health = await live_storage_adapter.health_check()
            if not supabase_health:
                pytest.skip("Supabase database not healthy")
            print(f"   ✅ Supabase database: Connected")
            
            print(f"🔄 Step 1: Creating chunks and generating embeddings...")
            for i in range(0, len(sentences), chunk_size):
                chunk_sentences = sentences[i:i + chunk_size]
                chunk_text = ' '.join(chunk_sentences)
                
                # Generate real embedding for this chunk
                embedding = await live_embedding_adapter.generate_embedding(chunk_text)
                
                chunk = DocumentChunk(
                    content=chunk_text,
                    chunk_index=i // chunk_size,
                    embedding=embedding,
                    metadata={
                        "chunk_size": len(chunk_text),
                        "sentence_count": len(chunk_sentences),
                        "chunk_type": "text_segment",
                        "embedding_model": "nomic-embed-text"
                    }
                )
                chunks.append(chunk)
                
                print(f"   ✅ Chunk {chunk.chunk_index}: {len(chunk_text)} chars, {len(embedding)} dims")
            
            # Create multi-chunk document
            content_hash = hashlib.sha256(long_text.encode()).hexdigest()
            multi_chunk_doc = Document(
                filename=f"multi_chunk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                file_path=Path("/test/multi_chunk_document.txt"),
                content_hash=content_hash,
                chunks=chunks,
                metadata={
                    "total_chunks": len(chunks),
                    "original_length": len(long_text),
                    "chunk_strategy": "sentence_based",
                    "test_type": "multi_chunk"
                }
            )
            
            # Store multi-chunk document
            print(f"🔄 Step 2: Storing multi-chunk document...")
            store_result = await live_storage_adapter.store_document(multi_chunk_doc)
            assert store_result is True, "Multi-chunk document storage should succeed"
            
            print(f"   ✅ Stored document with {len(chunks)} chunks")
            
            # Retrieve and verify
            print(f"🔄 Step 3: Retrieving and verifying multi-chunk document...")
            retrieved = await live_storage_adapter.retrieve_document(multi_chunk_doc.id)
            assert retrieved is not None, "Multi-chunk document should be retrievable"
            assert len(retrieved.chunks) == len(chunks), f"Should retrieve all {len(chunks)} chunks"
            
            # Verify chunk order and content
            for i, (original_chunk, retrieved_chunk) in enumerate(zip(chunks, retrieved.chunks)):
                assert retrieved_chunk.chunk_index == i, f"Chunk {i} should have correct index"
                assert retrieved_chunk.content == original_chunk.content, f"Chunk {i} content should match"
                
                # Verify embedding
                retrieved_embedding = retrieved_chunk.embedding
                if isinstance(retrieved_embedding, str):
                    import json
                    retrieved_embedding = json.loads(retrieved_embedding)
                
                assert len(retrieved_embedding) == 768, f"Chunk {i} should have 768-dimensional embedding"
                
                # Check embedding similarity
                similarity = np.dot(original_chunk.embedding, retrieved_embedding) / (
                    np.linalg.norm(original_chunk.embedding) * np.linalg.norm(retrieved_embedding)
                )
                assert similarity > 0.99, f"Chunk {i} embedding should be preserved (similarity: {similarity:.6f})"
                
                print(f"   ✅ Chunk {i}: Content and embedding verified")
            
            # Test similarity search across chunks
            print(f"🔄 Step 4: Testing similarity search across chunks...")
            query_text = "neural networks and deep learning models"
            query_embedding = await live_embedding_adapter.generate_embedding(query_text)
            
            chunk_similarities = []
            for chunk in retrieved.chunks:
                chunk_embedding = chunk.embedding
                if isinstance(chunk_embedding, str):
                    import json
                    chunk_embedding = json.loads(chunk_embedding)
                
                similarity = np.dot(query_embedding, chunk_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                )
                
                chunk_similarities.append((chunk, similarity))
                print(f"   Chunk {chunk.chunk_index} similarity: {similarity:.4f}")
            
            # Sort by similarity
            chunk_similarities.sort(key=lambda x: x[1], reverse=True)
            
            # The most similar chunk should contain relevant content
            most_similar_chunk = chunk_similarities[0][0]
            highest_similarity = chunk_similarities[0][1]
            
            print(f"   Most similar chunk: {most_similar_chunk.chunk_index} (similarity: {highest_similarity:.4f})")
            print(f"   Content preview: {most_similar_chunk.content[:100]}...")
            
            # Verify that the most similar chunk contains relevant keywords
            content_lower = most_similar_chunk.content.lower()
            relevant_keywords = ['neural', 'network', 'deep', 'learning', 'model', 'ai', 'artificial']
            found_keywords = [kw for kw in relevant_keywords if kw in content_lower]
            
            assert len(found_keywords) > 0, f"Most similar chunk should contain relevant keywords, found: {found_keywords}"
            print(f"   ✅ Found relevant keywords: {found_keywords}")
            
            print(f"\n🎉 Live Multi-chunk Processing Test PASSED!")
            print(f"   ✅ Multi-chunk document created: {len(chunks)} chunks")
            print(f"   ✅ All chunks stored and retrieved: Verified")
            print(f"   ✅ Embedding integrity: Verified")
            print(f"   ✅ Chunk-level similarity search: Working")
            
        finally:
            # Clean up
            if multi_chunk_doc and multi_chunk_doc.id:
                print(f"🧹 Cleaning up multi-chunk document...")
                try:
                    delete_result = await live_storage_adapter.delete_document(multi_chunk_doc.id)
                    if delete_result:
                        print(f"   ✅ Multi-chunk document deleted")
                    else:
                        print(f"   ⚠️  Multi-chunk document may not have been deleted")
                except Exception as e:
                    print(f"   ⚠️  Cleanup error: {e}")

    # Test 4: Live Performance and Batch Processing
    @pytest.mark.asyncio
    async def test_live_performance_batch_processing(
        self, 
        live_embedding_adapter, 
        live_storage_adapter
    ):
        """Test performance with batch processing using real services."""
        
        print(f"\n🧪 Testing Live Performance and Batch Processing")
        print("=" * 50)
        
        import time
        
        # Generate test texts
        num_docs = 10  # Reasonable number for live testing
        test_texts = [
            f"Performance test document {i}: This document contains information about "
            f"various topics including technology, science, and research. Document {i} "
            f"has unique content to ensure different embeddings are generated. "
            f"The content discusses artificial intelligence, machine learning, and "
            f"data processing techniques used in modern applications."
            for i in range(num_docs)
        ]
        
        documents = []
        
        try:
            # Test connections first
            print(f"🔄 Testing service connections...")
            
            # Test Ollama connection
            ollama_health = await live_embedding_adapter.health_check()
            if not ollama_health:
                pytest.skip("Ollama service not healthy")
            print(f"   ✅ Ollama service: Connected")
            
            # Test Supabase connection
            supabase_health = await live_storage_adapter.health_check()
            if not supabase_health:
                pytest.skip("Supabase database not healthy")
            print(f"   ✅ Supabase database: Connected")
            
            # Test batch embedding generation
            print(f"🔄 Step 1: Batch embedding generation ({num_docs} texts)...")
            start_time = time.time()
            
            embeddings = await live_embedding_adapter.generate_embeddings(test_texts)
            
            embedding_time = time.time() - start_time
            print(f"   ✅ Generated {len(embeddings)} embeddings in {embedding_time:.2f}s")
            print(f"   ⚡ Rate: {len(embeddings)/embedding_time:.1f} embeddings/second")
            
            # Verify all embeddings
            assert len(embeddings) == num_docs, f"Should generate {num_docs} embeddings"
            for i, embedding in enumerate(embeddings):
                assert len(embedding) == 768, f"Embedding {i} should be 768-dimensional"
                assert all(isinstance(x, (int, float)) for x in embedding), f"Embedding {i} should contain numeric values"
            
            # Create documents
            print(f"🔄 Step 2: Creating documents...")
            for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
                doc = Document(
                    filename=f"perf_test_{i}_{datetime.now().strftime('%H%M%S')}.txt",
                    file_path=Path(f"/test/perf_test_{i}.txt"),
                    content_hash=hashlib.sha256(text.encode()).hexdigest(),
                    chunks=[
                        DocumentChunk(
                            content=text,
                            chunk_index=0,
                            embedding=embedding,
                            metadata={
                                "performance_test": True,
                                "doc_index": i,
                                "batch_size": num_docs
                            }
                        )
                    ],
                    metadata={
                        "test_type": "performance",
                        "batch_size": num_docs,
                        "created_at": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            # Test batch storage
            print(f"🔄 Step 3: Batch document storage...")
            store_start = time.time()
            
            # Store documents concurrently
            store_tasks = [live_storage_adapter.store_document(doc) for doc in documents]
            store_results = await asyncio.gather(*store_tasks, return_exceptions=True)
            
            store_time = time.time() - store_start
            print(f"   ✅ Stored {num_docs} documents in {store_time:.2f}s")
            print(f"   ⚡ Rate: {num_docs/store_time:.1f} documents/second")
            
            # Verify all stores succeeded
            successful_stores = sum(1 for result in store_results if result is True)
            failed_stores = [i for i, result in enumerate(store_results) if isinstance(result, Exception)]
            
            print(f"   📊 Successful: {successful_stores}/{num_docs}")
            if failed_stores:
                print(f"   ⚠️  Failed stores: {failed_stores}")
                for i in failed_stores:
                    print(f"      Document {i}: {store_results[i]}")
            
            assert successful_stores >= num_docs * 0.8, f"At least 80% of stores should succeed"
            
            # Test batch retrieval
            print(f"🔄 Step 4: Batch document retrieval...")
            retrieve_start = time.time()
            
            # Only retrieve successfully stored documents
            successful_docs = [doc for i, doc in enumerate(documents) if store_results[i] is True]
            retrieve_tasks = [live_storage_adapter.retrieve_document(doc.id) for doc in successful_docs]
            retrieved_docs = await asyncio.gather(*retrieve_tasks, return_exceptions=True)
            
            retrieve_time = time.time() - retrieve_start
            print(f"   ✅ Retrieved {len(successful_docs)} documents in {retrieve_time:.2f}s")
            print(f"   ⚡ Rate: {len(successful_docs)/retrieve_time:.1f} documents/second")
            
            # Verify retrievals
            successful_retrievals = sum(1 for doc in retrieved_docs if isinstance(doc, Document))
            print(f"   📊 Successful retrievals: {successful_retrievals}/{len(successful_docs)}")
            
            # Test similarity search performance
            print(f"🔄 Step 5: Similarity search performance...")
            query_text = "artificial intelligence and machine learning research"
            query_embedding = await live_embedding_adapter.generate_embedding(query_text)
            
            similarity_start = time.time()
            
            similarities = []
            for doc in retrieved_docs:
                if isinstance(doc, Document) and doc.chunks:
                    doc_embedding = doc.chunks[0].embedding
                    if isinstance(doc_embedding, str):
                        import json
                        doc_embedding = json.loads(doc_embedding)
                    
                    similarity = np.dot(query_embedding, doc_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                    )
                    similarities.append((doc, similarity))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            similarity_time = time.time() - similarity_start
            
            print(f"   ✅ Computed similarities for {len(similarities)} documents in {similarity_time:.3f}s")
            print(f"   ⚡ Rate: {len(similarities)/similarity_time:.1f} comparisons/second")
            
            # Show top similarities
            print(f"   🏆 Top 3 similarities:")
            for i, (doc, sim) in enumerate(similarities[:3]):
                print(f"      {i+1}. {doc.filename}: {sim:.4f}")
            
            # Performance summary
            total_time = time.time() - start_time
            print(f"\n📊 Performance Summary:")
            print(f"   Total test time: {total_time:.2f}s")
            print(f"   Embedding generation: {embedding_time:.2f}s ({len(embeddings)/embedding_time:.1f}/s)")
            print(f"   Document storage: {store_time:.2f}s ({successful_stores/store_time:.1f}/s)")
            print(f"   Document retrieval: {retrieve_time:.2f}s ({successful_retrievals/retrieve_time:.1f}/s)")
            print(f"   Similarity computation: {similarity_time:.3f}s ({len(similarities)/similarity_time:.1f}/s)")
            
            # Performance assertions (lenient for live services)
            assert embedding_time < 60.0, f"Embedding generation should complete within 60s, took {embedding_time:.2f}s"
            assert store_time < 30.0, f"Document storage should complete within 30s, took {store_time:.2f}s"
            assert retrieve_time < 30.0, f"Document retrieval should complete within 30s, took {retrieve_time:.2f}s"
            assert similarity_time < 5.0, f"Similarity computation should complete within 5s, took {similarity_time:.3f}s"
            
            print(f"\n🎉 Live Performance Test PASSED!")
            print(f"   ✅ Batch embedding generation: {len(embeddings)} embeddings")
            print(f"   ✅ Concurrent storage: {successful_stores} documents")
            print(f"   ✅ Concurrent retrieval: {successful_retrievals} documents")
            print(f"   ✅ Similarity search: {len(similarities)} comparisons")
            
        finally:
            # Clean up all test documents
            print(f"🧹 Cleaning up performance test documents...")
            cleanup_count = 0
            for doc in documents:
                if doc.id:
                    try:
                        delete_result = await live_storage_adapter.delete_document(doc.id)
                        if delete_result:
                            cleanup_count += 1
                    except Exception as e:
                        print(f"   ⚠️  Failed to delete {doc.filename}: {e}")
            
            print(f"   ✅ Cleaned up {cleanup_count}/{len(documents)} documents")


if __name__ == "__main__":
    # Run live tests with verbose output
    pytest.main([
        __file__,
        "-v",
        "-s",
        "-m", "live",
        "--tb=short"
    ])