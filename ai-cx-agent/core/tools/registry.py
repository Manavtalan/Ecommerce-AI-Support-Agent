"""
Tool Registry
Manages and selects appropriate tools
"""

from typing import Dict, List, Optional
from core.tools.base import Tool
from core.tools.order_tool import OrderTool
from core.tools.knowledge_tool import KnowledgeTool


class ToolRegistry:
    """Manages all available tools"""
    
    def __init__(self, brand_name: str = "fashionhub"):
        """
        Initialize tool registry
        
        Args:
            brand_name: Brand name
        """
        self.brand_name = brand_name
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools"""
        # Order tool
        self.register(OrderTool(self.brand_name))
        
        # Knowledge tool
        self.register(KnowledgeTool(self.brand_name))
    
    def register(self, tool: Tool):
        """
        Register a tool
        
        Args:
            tool: Tool instance
        """
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get tool by name
        
        Args:
            name: Tool name
        
        Returns:
            Tool instance or None
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all available tools"""
        return list(self.tools.keys())
    
    def select_tool(self, query: str, intent: str = None) -> Optional[str]:
        """
        Select appropriate tool based on query and intent
        
        Args:
            query: User query
            intent: Detected intent (optional)
        
        Returns:
            Tool name or None
        """
        query_lower = query.lower()
        
        # Order-related keywords
        order_keywords = [
            "order", "tracking", "delivery", "shipped", "status",
            "where is", "when will", "track", "courier", "eta"
        ]
        
        # Policy/knowledge keywords
        knowledge_keywords = [
            "policy", "return", "refund", "exchange", "shipping",
            "cancel", "how to", "can i", "what if", "do you"
        ]
        
        # Check for order queries
        if any(keyword in query_lower for keyword in order_keywords):
            # Check if order ID mentioned
            import re
            if re.search(r'\b\d{4,}\b', query):
                return "get_order_status"
        
        # Check for policy queries
        if any(keyword in query_lower for keyword in knowledge_keywords):
            return "search_knowledge"
        
        # Default to knowledge for questions
        if query.strip().endswith("?"):
            return "search_knowledge"
        
        return None
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict:
        """
        Execute a tool
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters
        
        Returns:
            Tool result
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "tool": tool_name
            }
        
        return tool.execute(**kwargs)
    
    def __repr__(self) -> str:
        return f"ToolRegistry(tools={list(self.tools.keys())})"


# Convenience function
def create_tool_registry(brand_name: str = "fashionhub") -> ToolRegistry:
    """
    Create tool registry
    
    Args:
        brand_name: Brand name
    
    Returns:
        ToolRegistry instance
    """
    return ToolRegistry(brand_name)
