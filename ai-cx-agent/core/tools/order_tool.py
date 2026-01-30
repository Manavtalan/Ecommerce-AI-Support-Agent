"""
Order Tool
Fetches order information from Shopify
"""

from typing import Dict, Any
from core.tools.base import Tool
from core.integrations.shopify.sync import ShopifyOrderSync


class OrderTool(Tool):
    """Get order status and details"""
    
    def __init__(self, brand_name: str = "fashionhub"):
        """
        Initialize order tool
        
        Args:
            brand_name: Brand name
        """
        super().__init__(
            name="get_order_status",
            description="Get order status, tracking, and details from Shopify"
        )
        self.sync = ShopifyOrderSync(brand_name)
    
    def validate_params(self, **kwargs) -> tuple[bool, str]:
        """Validate order_id parameter"""
        order_id = kwargs.get("order_id")
        
        if not order_id:
            return False, "order_id is required"
        
        return True, None
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Get order status
        
        Args:
            order_id: Order ID or number
        
        Returns:
            Order details or error
        """
        # Validate
        is_valid, error = self.validate_params(**kwargs)
        if not is_valid:
            return self.format_result(False, error=error)
        
        order_id = kwargs["order_id"]
        
        try:
            # Fetch from Shopify
            order = self.sync.get_order(order_id)
            
            if not order:
                return self.format_result(
                    False,
                    error=f"Order {order_id} not found"
                )
            
            # Return formatted order data
            return self.format_result(True, data=order)
            
        except Exception as e:
            return self.format_result(
                False,
                error=f"Failed to fetch order: {str(e)}"
            )


# Convenience function
def get_order_status(order_id: str, brand_name: str = "fashionhub") -> Dict:
    """
    Get order status
    
    Args:
        order_id: Order ID
        brand_name: Brand name
    
    Returns:
        Order details
    """
    tool = OrderTool(brand_name)
    return tool.execute(order_id=order_id)
