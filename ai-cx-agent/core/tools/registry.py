"""
Tool Registry - WITH RETRY LOGIC
Manages and executes tools with graceful failure handling
"""

from typing import Dict, List, Optional
import re
import time


class ToolRegistry:
    """Registry for available tools with retry logic"""
    
    def __init__(self, brand_id: str = "fashionhub"):
        """Initialize tool registry"""
        self.brand_id = brand_id
        self.tools = {}
        self.retry_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'retries': 0
        }
        
        # Register available tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        from core.tools.order_status import get_order_status
        from core.tools.knowledge_search import search_knowledge
        from core.tools.product_info import get_product_info
        from core.tools.shipping_checker import check_shipping_eligibility
        
        self.tools = {
            "get_order_status": {
                "function": get_order_status,
                "description": "Get order status and tracking info",
                "parameters": ["order_id"],
                "keywords": ["order", "track", "status", "where", "delivery", "shipped"]
            },
            "search_knowledge": {
                "function": search_knowledge,
                "description": "Search knowledge base for policies and info",
                "parameters": ["query", "brand_id"],
                "keywords": ["policy", "return", "refund", "exchange", "shipping", "warranty", "cancel"]
            },
            "get_product_info": {
                "function": get_product_info,
                "description": "Get product details and availability",
                "parameters": ["product_id"],
                "keywords": ["product", "item", "details", "available", "stock", "price"]
            },
            "check_shipping_eligibility": {
                "function": check_shipping_eligibility,
                "description": "Check if shipping available to location",
                "parameters": ["pincode"],
                "keywords": ["ship", "deliver", "pincode", "location", "available"]
            }
        }
    
    def select_tool(self, user_message: str) -> Optional[str]:
        """Select appropriate tool based on user message"""
        message_lower = user_message.lower()
        
        # Check each tool's keywords
        for tool_name, tool_info in self.tools.items():
            keywords = tool_info["keywords"]
            if any(keyword in message_lower for keyword in keywords):
                return tool_name
        
        return None
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict:
        """
        Execute tool (single attempt, no retry)
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters
        
        Returns:
            {success: bool, data: dict, error: str}
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "data": None,
                "error": f"Tool '{tool_name}' not found"
            }
        
        tool_info = self.tools[tool_name]
        tool_function = tool_info["function"]
        
        try:
            # Add brand_id if tool needs it
            if "brand_id" in tool_info["parameters"]:
                kwargs["brand_id"] = self.brand_id
            
            # Execute tool
            result = tool_function(**kwargs)
            
            return {
                "success": True,
                "data": result,
                "error": None
            }
        
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }
    
    def execute_with_retry(
        self,
        tool_name: str,
        max_retries: int = 1,
        **kwargs
    ) -> Dict:
        """
        Execute tool with retry logic
        
        Args:
            tool_name: Name of tool to execute
            max_retries: Maximum retry attempts (default: 1)
            **kwargs: Tool parameters
        
        Returns:
            {
                success: bool,
                data: dict,
                error: str,
                retries: int,
                fallback_message: str (optional)
            }
        """
        self.retry_stats['total_executions'] += 1
        
        retries = 0
        last_error = None
        
        while retries <= max_retries:
            try:
                result = self.execute_tool(tool_name, **kwargs)
                
                if result["success"]:
                    # Success!
                    self.retry_stats['successful_executions'] += 1
                    if retries > 0:
                        print(f"   ✅ Tool retry successful after {retries} attempt(s)")
                    
                    return {
                        **result,
                        'retries': retries
                    }
                else:
                    # Tool returned failure
                    last_error = result["error"]
                    error_type = self._classify_error(last_error)
                    
                    # Check if retryable
                    if self._is_retryable_error(error_type) and retries < max_retries:
                        retries += 1
                        self.retry_stats['retries'] += 1
                        
                        print(f"   ⏳ Tool error ({error_type}), retrying... (attempt {retries}/{max_retries})")
                        time.sleep(1)  # Brief wait before retry
                        continue
                    else:
                        # Not retryable or max retries reached
                        break
            
            except Exception as e:
                last_error = str(e)
                error_type = self._classify_error(last_error)
                
                if self._is_retryable_error(error_type) and retries < max_retries:
                    retries += 1
                    self.retry_stats['retries'] += 1
                    
                    print(f"   ⏳ Tool exception ({error_type}), retrying... (attempt {retries}/{max_retries})")
                    time.sleep(1)
                    continue
                else:
                    break
        
        # All retries failed
        self.retry_stats['failed_executions'] += 1
        
        # Build fallback message
        fallback_message = self._build_fallback_message(tool_name, last_error)
        
        return {
            'success': False,
            'data': None,
            'error': last_error,
            'retries': retries,
            'fallback_message': fallback_message
        }
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error type from error message"""
        error_lower = error_message.lower() if error_message else ""
        
        if 'timeout' in error_lower:
            return 'timeout'
        elif 'connection' in error_lower or 'network' in error_lower:
            return 'connection'
        elif 'not found' in error_lower or '404' in error_lower:
            return 'not_found'
        elif 'unauthorized' in error_lower or '401' in error_lower:
            return 'auth'
        elif 'rate limit' in error_lower or '429' in error_lower:
            return 'rate_limit'
        elif 'internal server' in error_lower or '500' in error_lower:
            return 'server_error'
        else:
            return 'unknown'
    
    def _is_retryable_error(self, error_type: str) -> bool:
        """Determine if error should be retried"""
        retryable = ['timeout', 'connection', 'rate_limit', 'server_error']
        return error_type in retryable
    
    def _build_fallback_message(self, tool_name: str, error: str) -> str:
        """Build user-friendly fallback message"""
        
        error_type = self._classify_error(error)
        
        if error_type in ['timeout', 'connection']:
            if tool_name == 'get_order_status':
                return "I'm having trouble accessing your order details right now. Could you provide your email address so I can look it up another way?"
            else:
                return "I'm having trouble accessing that information right now. Let me connect you with our support team."
        
        if error_type == 'not_found':
            if tool_name == 'get_order_status':
                return "I couldn't find that order number. Could you verify the order number or provide the email address used for the order?"
            else:
                return "I couldn't find information about that. Let me connect you with our support team."
        
        if error_type == 'auth':
            return "I'm experiencing an authentication issue. Let me connect you with our support team who can help."
        
        if error_type == 'rate_limit':
            return "We're experiencing high traffic right now. Please give me a moment and I'll try again."
        
        # Generic fallback
        if tool_name == 'get_order_status':
            return "I'm unable to retrieve your order details at the moment. Let me connect you with our support team."
        else:
            return "I want to give you accurate information. Let me connect you with our support team."
    
    def list_tools(self) -> List[str]:
        """Get list of available tools"""
        return list(self.tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """Get information about a specific tool"""
        return self.tools.get(tool_name)
    
    def get_retry_stats(self) -> Dict:
        """Get retry statistics"""
        total = self.retry_stats['total_executions']
        success_rate = (self.retry_stats['successful_executions'] / total * 100) if total > 0 else 0
        
        return {
            **self.retry_stats,
            'success_rate': round(success_rate, 1)
        }
    
    def __repr__(self) -> str:
        return f"ToolRegistry(brand={self.brand_id}, tools={len(self.tools)})"
