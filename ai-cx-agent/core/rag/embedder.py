"""
Document Embedder
Generates embeddings and stores in Qdrant
"""

import os
from typing import List, Dict
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
from core.rag.config import (
    QDRANT_HOST, QDRANT_PORT, EMBEDDING_MODEL, 
    EMBEDDING_DIMENSIONS, get_collection_name
)
from core.rag.chunker import DocumentChunker

load_dotenv()


class DocumentEmbedder:
    """Embeds documents and stores in Qdrant"""
    
    def __init__(self, brand_name: str):
        """
        Initialize embedder
        
        Args:
            brand_name: Brand name (e.g., 'fashionhub')
        """
        self.brand_name = brand_name
        self.collection_name = get_collection_name(brand_name)
        
        # Initialize clients
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Initialize chunker
        self.chunker = DocumentChunker()
    
    def create_collection(self):
        """Create Qdrant collection for brand"""
        try:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Created collection: {self.collection_name}")
        except Exception as e:
            print(f"   Collection exists or error: {e}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    
    def embed_chunks(self, chunks: List[Dict]) -> List[PointStruct]:
        """
        Embed multiple chunks
        
        Args:
            chunks: List of text chunks with metadata
        
        Returns:
            List of Qdrant points
        """
        points = []
        
        print(f"🔄 Embedding {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = self.embed_text(chunk['text'])
            
            # Create Qdrant point
            point = PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "text": chunk['text'],
                    "source": chunk['metadata']['source'],
                    "brand": chunk['metadata']['brand'],
                    "type": chunk['metadata']['type'],
                    "category": chunk['metadata']['category'],
                    "chunk_index": chunk['chunk_index'],
                    "token_count": chunk['token_count']
                }
            )
            
            points.append(point)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"   Embedded {i + 1}/{len(chunks)} chunks")
        
        print(f"✅ Embedded all {len(chunks)} chunks")
        return points
    
    def store_embeddings(self, points: List[PointStruct]):
        """
        Store embeddings in Qdrant
        
        Args:
            points: List of Qdrant points
        """
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"✅ Stored {len(points)} embeddings in Qdrant")
    
    def embed_and_store_policies(self):
        """
        Complete pipeline: chunk → embed → store
        """
        print(f"\n🚀 Starting embedding pipeline for {self.brand_name}")
        print("=" * 60)
        
        # Step 1: Create collection
        print("\n1️⃣ Creating collection...")
        self.create_collection()
        
        # Step 2: Chunk documents
        print("\n2️⃣ Chunking documents...")
        chunks = self.chunker.chunk_all_policies(self.brand_name)
        
        # Step 3: Generate embeddings
        print("\n3️⃣ Generating embeddings...")
        points = self.embed_chunks(chunks)
        
        # Step 4: Store in Qdrant
        print("\n4️⃣ Storing in Qdrant...")
        self.store_embeddings(points)
        
        print("\n" + "=" * 60)
        print(f"🎉 Embedding pipeline complete!")
        print(f"   Brand: {self.brand_name}")
        print(f"   Collection: {self.collection_name}")
        print(f"   Chunks stored: {len(points)}")
        print()
    
    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        try:
            collection = self.qdrant_client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": collection.vectors_count,
                "points_count": collection.points_count,
                "status": collection.status
            }
        except Exception as e:
            return {"error": str(e)}


# Convenience function
def embed_brand_knowledge(brand_name: str):
    """
    Embed all knowledge for a brand
    
    Args:
        brand_name: Brand name (e.g., 'fashionhub')
    """
    embedder = DocumentEmbedder(brand_name)
    embedder.embed_and_store_policies()
