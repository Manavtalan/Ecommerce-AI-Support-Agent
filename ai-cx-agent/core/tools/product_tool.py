"""
Product Tool
Fetches product information from Shopify
"""

from typing import Dict, Any
from core.tools.base import Tool
from core.integrations.shopify.client import ShopifyClient


class ProductTool(Tool):
    """Get product information from Shopify"""
    
    def __init__(self, brand_name: str = "fashionhub"):
        """
        Initialize product tool
        
        Args:
            brand_name: Brand name
        """
        super().__init__(
            name="get_product_info",
            description="Get product details, pricing, and availability from Shopify"
        )
        self.client = ShopifyClient()
    
    def validate_params(self, **kwargs) -> tuple[bool, str]:
        """Validate product_id or product_name"""
        product_id = kwargs.get("product_id")
        product_name = kwargs.get("product_name")
        
        if not product_id and not product_name:
            return False, "product_id or product_name is required"
        
        return True, None
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Get product information
        
        Args:
            product_id: Shopify product ID (optional)
            product_name: Product name to search (optional)
        
        Returns:
            Product details or error
        """
        # Validate
        is_valid, error = self.validate_params(**kwargs)
        if not is_valid:
            return self.format_result(False, error=error)
        
        product_id = kwargs.get("product_id")
        
        try:
            if product_id:
                # Fetch by ID
                product = self.client.get_product(product_id)
                
                if not product:
                    return self.format_result(
                        False,
                        error=f"Product {product_id} not found"
                    )
                
                return self.format_result(True, data=product)
            else:
                # Search by name would require additional API call
                # For now, return error suggesting to use product ID
                return self.format_result(
                    False,
                    error="Product search by name not yet implemented. Please provide product_id."
                )
            
        except Exception as e:
            return self.format_result(
                False,
                error=f"Failed to fetch product: {str(e)}"
            )


# Convenience function
def get_product_info(product_id: str) -> Dict:
    """
    Get product information
    
    Args:
        product_id: Product ID
    
    Returns:
        Product details
    """
    tool = ProductTool()
    return tool.execute(product_id=product_id)
