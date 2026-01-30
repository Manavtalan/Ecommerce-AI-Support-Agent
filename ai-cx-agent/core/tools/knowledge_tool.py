"""
Knowledge Tool
Searches knowledge base using RAG
"""

from typing import Dict, Any
from core.tools.base import Tool
from core.rag.retriever import KnowledgeRetriever


class KnowledgeTool(Tool):
    """Search knowledge base for policies and FAQs"""
    
    def __init__(self, brand_name: str = "fashionhub"):
        """
        Initialize knowledge tool
        
        Args:
            brand_name: Brand name
        """
        super().__init__(
            name="search_knowledge",
            description="Search policy documents and FAQs"
        )
        self.retriever = KnowledgeRetriever(brand_name)
    
    def validate_params(self, **kwargs) -> tuple[bool, str]:
        """Validate query parameter"""
        query = kwargs.get("query")
        
        if not query:
            return False, "query is required"
        
        if len(query.strip()) < 3:
            return False, "query too short (min 3 characters)"
        
        return True, None
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Search knowledge base
        
        Args:
            query: Search query
            top_k: Number of results (optional)
        
        Returns:
            Search results or error
        """
        # Validate
        is_valid, error = self.validate_params(**kwargs)
        if not is_valid:
            return self.format_result(False, error=error)
        
        query = kwargs["query"]
        top_k = kwargs.get("top_k", 3)
        
        try:
            # Search knowledge base
            result = self.retriever.retrieve_with_confidence(query, top_k=top_k)
            
            if not result["found"]:
                return self.format_result(
                    False,
                    error="No relevant information found"
                )
            
            # Format results
            formatted_results = {
                "confidence": result["confidence"],
                "action": result["action"],
                "top_score": result["top_score"],
                "results": result["results"]
            }
            
            return self.format_result(True, data=formatted_results)
            
        except Exception as e:
            return self.format_result(
                False,
                error=f"Search failed: {str(e)}"
            )


# Convenience function
def search_knowledge(query: str, brand_name: str = "fashionhub") -> Dict:
    """
    Search knowledge base
    
    Args:
        query: Search query
        brand_name: Brand name
    
    Returns:
        Search results
    """
    tool = KnowledgeTool(brand_name)
    return tool.execute(query=query)
