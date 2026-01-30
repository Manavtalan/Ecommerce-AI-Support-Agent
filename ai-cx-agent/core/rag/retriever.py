"""
Knowledge Retriever
Semantic search over embedded knowledge base
"""

import os
from typing import List, Dict, Optional
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv
from core.rag.config import (
    QDRANT_HOST, QDRANT_PORT, EMBEDDING_MODEL,
    DEFAULT_TOP_K, SIMILARITY_THRESHOLD_HIGH,
    SIMILARITY_THRESHOLD_MEDIUM, SIMILARITY_THRESHOLD_LOW,
    get_collection_name
)

load_dotenv()


class KnowledgeRetriever:
    """Retrieves relevant knowledge using semantic search"""
    
    def __init__(self, brand_name: str):
        """
        Initialize retriever
        
        Args:
            brand_name: Brand name (e.g., 'fashionhub')
        """
        self.brand_name = brand_name
        self.collection_name = get_collection_name(brand_name)
        
        # Initialize clients
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for query
        
        Args:
            query: Search query
        
        Returns:
            Query embedding vector
        """
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query
        )
        return response.data[0].embedding
    
    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Semantic search in knowledge base
        
        Args:
            query: Search query
            top_k: Number of results to return
            category: Optional category filter (e.g., 'return', 'shipping')
        
        Returns:
            List of relevant chunks with scores
        """
        # Generate query embedding
        query_vector = self.embed_query(query)
        
        # Build filter if category specified
        search_filter = None
        if category:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category)
                    )
                ]
            )
        
        # Search using query_points() - correct method for this Qdrant version
        results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=search_filter
        )
        
        # Format results (note: results.points not just results)
        formatted_results = []
        for result in results.points:
            formatted_results.append({
                "text": result.payload["text"],
                "score": result.score,
                "source": result.payload["source"],
                "category": result.payload["category"],
                "chunk_index": result.payload["chunk_index"]
            })
        
        return formatted_results
    
    def retrieve_with_confidence(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K
    ) -> Dict:
        """
        Retrieve with confidence scoring
        
        Args:
            query: Search query
            top_k: Number of results
        
        Returns:
            Results with confidence assessment
        """
        # Search
        results = self.search(query, top_k=top_k)
        
        if not results:
            return {
                "found": False,
                "confidence": "none",
                "action": "escalate",
                "message": "No relevant information found in knowledge base",
                "results": []
            }
        
        # Get top score
        top_score = results[0]["score"]
        
        # Determine confidence
        if top_score >= SIMILARITY_THRESHOLD_HIGH:
            confidence = "high"
            action = "answer"
        elif top_score >= SIMILARITY_THRESHOLD_MEDIUM:
            confidence = "medium"
            action = "answer_with_caveat"
        elif top_score >= SIMILARITY_THRESHOLD_LOW:
            confidence = "low"
            action = "clarify"
        else:
            confidence = "very_low"
            action = "escalate"
        
        return {
            "found": True,
            "confidence": confidence,
            "action": action,
            "top_score": top_score,
            "results": results
        }
    
    def get_policy_answer(self, query: str) -> Dict:
        """
        Get answer to policy question
        
        Args:
            query: Policy question
        
        Returns:
            Answer with metadata
        """
        retrieval = self.retrieve_with_confidence(query)
        
        if not retrieval["found"] or retrieval["action"] == "escalate":
            return {
                "answer": None,
                "confidence": retrieval["confidence"],
                "action": "escalate",
                "message": "I don't have clear information on that. Let me connect you with our team."
            }
        
        # Combine top results
        combined_text = "\n\n".join([r["text"] for r in retrieval["results"][:3]])
        
        return {
            "answer": combined_text,
            "confidence": retrieval["confidence"],
            "action": retrieval["action"],
            "sources": [r["source"] for r in retrieval["results"][:3]],
            "top_score": retrieval["top_score"]
        }


# Convenience function
def search_knowledge(brand_name: str, query: str, top_k: int = 3) -> List[Dict]:
    """
    Search knowledge base
    
    Args:
        brand_name: Brand name
        query: Search query
        top_k: Number of results
    
    Returns:
        Search results
    """
    retriever = KnowledgeRetriever(brand_name)
    return retriever.search(query, top_k=top_k)
