"""
Tool Registry - FIXED SELECTION LOGIC
"""

from typing import Dict, List, Optional
from core.tools.base import Tool
from core.tools.order_tool import OrderTool
from core.tools.knowledge_tool import KnowledgeTool
from core.tools.product_tool import ProductTool
from core.tools.shipping_tool import ShippingTool


class ToolRegistry:
    """Manages all available tools"""
    
    def __init__(self, brand_name: str = "fashionhub"):
        self.brand_name = brand_name
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        self.register(OrderTool(self.brand_name))
        self.register(KnowledgeTool(self.brand_name))
        self.register(ProductTool(self.brand_name))
        self.register(ShippingTool(self.brand_name))
    
    def register(self, tool: Tool):
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        return list(self.tools.keys())
    
    def select_tool(self, query: str, intent: str = None) -> Optional[str]:
        """Select appropriate tool - IMPROVED LOGIC"""
        import re
        query_lower = query.lower()
        
        # Check for 6-digit pincode FIRST (shipping takes priority over order ID)
        has_pincode = bool(re.search(r'\b\d{6}\b', query))
        
        # Shipping keywords
        shipping_keywords = [
            "ship to", "deliver to", "delivery to", "pincode", "pin code",
            "cod", "cash on delivery", "shipping cost", "delivery charge",
            "free shipping", "do you deliver", "can you ship"
        ]
        
        # If has pincode OR shipping keywords, use shipping tool
        if has_pincode or any(keyword in query_lower for keyword in shipping_keywords):
            return "check_shipping_eligibility"
        
        # Order keywords
        order_keywords = [
            "order", "tracking", "shipped", "delivery status",
            "where is", "when will", "track", "courier", "eta"
        ]
        
        # Check for order ID (4-5 digits)
        has_order_id = bool(re.search(r'\b\d{4,5}\b', query))
        
        # If has order ID, use order tool
        if has_order_id and any(keyword in query_lower for keyword in order_keywords):
            return "get_order_status"
        
        # Product keywords
        product_keywords = [
            "product", "price", "stock", "available", "size",
            "color", "variant", "buy", "purchase"
        ]
        
        if any(keyword in query_lower for keyword in product_keywords):
            return "get_product_info"
        
        # Policy/knowledge keywords
        knowledge_keywords = [
            "policy", "return", "refund", "exchange",
            "cancel", "how to", "can i", "what if", "do you",
            "what is", "what's"
        ]
        
        if any(keyword in query_lower for keyword in knowledge_keywords):
            return "search_knowledge"
        
        # Questions default to knowledge
        if query.strip().endswith("?"):
            return "search_knowledge"
        
        return None
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict:
        tool = self.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found", "tool": tool_name}
        return tool.execute(**kwargs)
    
    def __repr__(self) -> str:
        return f"ToolRegistry(tools={list(self.tools.keys())})"
