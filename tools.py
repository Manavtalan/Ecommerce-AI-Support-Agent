# tools.py
"""
Tool Functions for AI Agent
Provides deterministic business logic and data access.
"""

from orders_db import ORDERS


def get_order_status(order_id: str) -> dict:
    """
    Fetch order details by order ID from database.
    
    This is the source of truth for order information.
    Returns actual order data - never guess or hallucinate.
    
    Args:
        order_id: The order number to look up (as string)
        
    Returns:
        Dictionary with order details if found, None if not found
        
    Example:
        {
            "status": "Shipped",
            "courier": "Delhivery",
            "tracking_url": "https://...",
            "estimated_delivery": "2026-01-18"
        }
    """
    return ORDERS.get(order_id)
