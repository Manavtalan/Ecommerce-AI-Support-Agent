"""
Order Status Tool - WITH TEST DATA FALLBACK
Gets order status from Shopify OR test data
"""

from typing import Dict, Optional
import json
from pathlib import Path


def get_order_status(order_id: str, brand_id: str = "fashionhub") -> Dict:
    """
    Get order status and details
    
    Args:
        order_id: Order ID to look up
        brand_id: Brand identifier
    
    Returns:
        Dict with order information
    """
    
    # Try to load from test data first
    test_data_path = Path(f"test_data/orders/{brand_id}_orders.json")
    
    if test_data_path.exists():
        try:
            with open(test_data_path, 'r') as f:
                orders = json.load(f)
            
            if order_id in orders:
                order = orders[order_id]
                
                # Format response
                return {
                    "success": True,
                    "order_id": order_id,
                    "status": order.get("status"),
                    "customer_name": order.get("customer_name"),
                    "customer_email": order.get("customer_email"),
                    "order_date": order.get("order_date"),
                    "items": order.get("items", []),
                    "total": order.get("total"),
                    "shipping": order.get("shipping", {}),
                    "payment_method": order.get("payment_method"),
                    "notes": order.get("notes", ""),
                    "source": "test_data"
                }
        except Exception as e:
            print(f"Error reading test data: {e}")
    
    # If not found in test data, try Shopify (for production)
    try:
        from core.integrations.shopify.client import ShopifyClient
        
        client = ShopifyClient(brand_id=brand_id)
        shopify_order = client.get_order(order_id)
        
        if shopify_order:
            return {
                "success": True,
                "order_id": order_id,
                "status": shopify_order.get("financial_status"),
                "customer_name": shopify_order.get("customer", {}).get("name"),
                "customer_email": shopify_order.get("customer", {}).get("email"),
                "order_date": shopify_order.get("created_at"),
                "items": shopify_order.get("line_items", []),
                "total": shopify_order.get("total_price"),
                "shipping": shopify_order.get("shipping_address", {}),
                "source": "shopify"
            }
    except Exception as e:
        print(f"Shopify lookup failed: {e}")
    
    # Order not found
    return {
        "success": False,
        "error": f"Order {order_id} not found",
        "message": f"I couldn't find order #{order_id} in our system. Could you please verify the order number?",
        "suggestions": [
            "Check if the order number is correct",
            "The order number is usually in your confirmation email",
            "You can also check your account order history"
        ]
    }


# For backward compatibility
def get_order_status_legacy(order_id: str) -> Dict:
    """Legacy function - calls main function with default brand"""
    return get_order_status(order_id, "fashionhub")


# Test function
def test_order_tool():
    """Test the order tool"""
    print("🧪 TESTING ORDER TOOL")
    print("=" * 70)
    print()
    
    # Test 1: Existing order
    print("TEST 1: Order 12345 (Should exist)")
    result = get_order_status("12345", "fashionhub")
    print(f"Success: {result.get('success')}")
    print(f"Status: {result.get('status')}")
    print(f"Customer: {result.get('customer_name')}")
    print(f"Source: {result.get('source')}")
    print()
    
    # Test 2: Another existing order
    print("TEST 2: Order 12346 (Should exist)")
    result = get_order_status("12346", "fashionhub")
    print(f"Success: {result.get('success')}")
    print(f"Status: {result.get('status')}")
    print(f"Customer: {result.get('customer_name')}")
    print()
    
    # Test 3: Non-existent order
    print("TEST 3: Order 99999 (Should not exist)")
    result = get_order_status("99999", "fashionhub")
    print(f"Success: {result.get('success')}")
    print(f"Error: {result.get('error')}")
    print(f"Message: {result.get('message')}")
    print()
    
    print("=" * 70)
    print("✅ Order tool tests complete!")


if __name__ == "__main__":
    test_order_tool()
