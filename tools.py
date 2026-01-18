# tools.py

from orders_db import ORDERS

def get_order_status(order_id: str):
    """
    Fetch order details by order ID.
    Returns order data dict or None.
    """
    return ORDERS.get(order_id)
