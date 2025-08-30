#!/usr/bin/env python3
"""
Create sample data in Supabase for testing and exploration.
"""

import os
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def create_sample_data():
    """Create sample documents in Supabase."""
    print("📝 Creating Sample Data in Supabase")
    print("=" * 40)
    
    # Import the live adapter
    from tests.integration.test_live_supabase_integration import LiveSupabaseStorageAdapter
    from src.config import get_supabase_config
    from src.domain.models.document import Document, DocumentChunk
    
    # Create configuration
    config = get_supabase_config()
    
    adapter = LiveSupabaseStorageAdapter(config)
    
    # Create sample documents
    documents = []
    
    # Document 1: Technology document
    doc1 = Document(
        filename="ai_machine_learning_guide.txt",
        file_path=Path("/samples/ai_machine_learning_guide.txt"),
        content_hash=f"tech_hash_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        chunks=[
            DocumentChunk(
                content="Artificial Intelligence and Machine Learning are transforming how we process and understand data. These technologies enable computers to learn patterns from large datasets and make predictions or decisions without explicit programming.",
                chunk_index=0,
                embedding=[0.8, 0.6, 0.4, 0.2] + [0.1] * 764,  # Tech-focused embedding
                metadata={
                    "topic": "AI/ML",
                    "difficulty": "intermediate",
                    "keywords": ["artificial intelligence", "machine learning", "data"]
                }
            ),
            DocumentChunk(
                content="Deep learning, a subset of machine learning, uses neural networks with multiple layers to model and understand complex patterns. This approach has revolutionized fields like computer vision, natural language processing, and speech recognition.",
                chunk_index=1,
                embedding=[0.7, 0.8, 0.5, 0.3] + [0.05] * 764,  # Similar but different
                metadata={
                    "topic": "deep learning",
                    "difficulty": "advanced",
                    "keywords": ["deep learning", "neural networks", "computer vision"]
                }
            )
        ],
        metadata={
            "category": "technology",
            "author": "AI Research Team",
            "created_for": "sample_exploration",
            "tags": ["AI", "ML", "technology", "guide"]
        }
    )
    
    # Document 2: Cooking document (different domain)
    doc2 = Document(
        filename="italian_pasta_recipes.txt",
        file_path=Path("/samples/italian_pasta_recipes.txt"),
        content_hash=f"cooking_hash_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        chunks=[
            DocumentChunk(
                content="Traditional Italian pasta is made with just two ingredients: durum wheat semolina and water. The key to perfect pasta is the quality of the wheat and the proper kneading technique to develop the gluten structure.",
                chunk_index=0,
                embedding=[0.2, 0.1, 0.9, 0.8] + [0.02] * 764,  # Cooking-focused embedding
                metadata={
                    "topic": "pasta making",
                    "cuisine": "italian",
                    "difficulty": "beginner",
                    "keywords": ["pasta", "italian", "cooking", "recipe"]
                }
            ),
            DocumentChunk(
                content="For a classic carbonara, you need eggs, pecorino romano cheese, guanciale, and black pepper. The secret is to create a creamy sauce without scrambling the eggs by controlling the temperature carefully.",
                chunk_index=1,
                embedding=[0.1, 0.2, 0.8, 0.9] + [0.01] * 764,  # Similar cooking theme
                metadata={
                    "topic": "carbonara recipe",
                    "cuisine": "italian",
                    "difficulty": "intermediate",
                    "keywords": ["carbonara", "eggs", "cheese", "technique"]
                }
            )
        ],
        metadata={
            "category": "cooking",
            "author": "Chef Marco",
            "created_for": "sample_exploration",
            "tags": ["cooking", "italian", "pasta", "recipes"]
        }
    )
    
    # Document 3: Science document
    doc3 = Document(
        filename="quantum_physics_basics.txt",
        file_path=Path("/samples/quantum_physics_basics.txt"),
        content_hash=f"science_hash_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        chunks=[
            DocumentChunk(
                content="Quantum mechanics describes the behavior of matter and energy at the atomic and subatomic level. Unlike classical physics, quantum systems can exist in multiple states simultaneously, a phenomenon called superposition.",
                chunk_index=0,
                embedding=[0.5, 0.9, 0.2, 0.7] + [0.03] * 764,  # Science-focused embedding
                metadata={
                    "topic": "quantum mechanics",
                    "field": "physics",
                    "difficulty": "advanced",
                    "keywords": ["quantum", "physics", "superposition", "mechanics"]
                }
            )
        ],
        metadata={
            "category": "science",
            "author": "Dr. Physics",
            "created_for": "sample_exploration",
            "tags": ["science", "physics", "quantum", "education"]
        }
    )
    
    documents = [doc1, doc2, doc3]
    
    # Store all documents
    stored_docs = []
    for i, doc in enumerate(documents, 1):
        print(f"\n📄 Storing document {i}: {doc.filename}")
        try:
            result = await adapter.store_document(doc)
            if result:
                print(f"✅ Successfully stored '{doc.filename}' (ID: {doc.id})")
                stored_docs.append(doc)
            else:
                print(f"❌ Failed to store '{doc.filename}'")
        except Exception as e:
            print(f"❌ Error storing '{doc.filename}': {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Documents created: {len(stored_docs)}")
    print(f"   Total chunks: {sum(len(doc.chunks) for doc in stored_docs)}")
    
    if stored_docs:
        print(f"\n🔍 You can now explore the data:")
        print(f"   1. Run: python explore_supabase_readonly.py")
        print(f"   2. Go to Supabase dashboard → Table Editor → documents")
        print(f"   3. Run similarity searches with the test functions")
        
        print(f"\n📋 Created Documents:")
        for doc in stored_docs:
            print(f"   - {doc.filename} (ID: {doc.id})")
            print(f"     Category: {doc.metadata.get('category')}")
            print(f"     Chunks: {len(doc.chunks)}")
    
    return stored_docs

def main():
    """Main function."""
    asyncio.run(create_sample_data())

if __name__ == "__main__":
    main()