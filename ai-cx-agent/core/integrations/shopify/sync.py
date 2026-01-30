"""
Shopify Order Sync
Syncs orders from Shopify to local format
"""

from typing import Dict, List, Optional
from core.integrations.shopify.client import ShopifyClient
from core.integrations.shopify.mapper import ShopifyOrderMapper


class ShopifyOrderSync:
    """Syncs orders from Shopify"""
    
    def __init__(self, brand_name: str = "fashionhub"):
        """
        Initialize sync
        
        Args:
            brand_name: Brand name
        """
        self.brand_name = brand_name
        self.client = ShopifyClient()
        self.mapper = ShopifyOrderMapper()
        self.orders_cache = {}
    
    def sync_orders(self, limit: int = 50) -> Dict[str, Dict]:
        """
        Sync orders from Shopify
        
        Args:
            limit: Max orders to sync
        
        Returns:
            Dict of order_id -> order data
        """
        print(f"🔄 Syncing orders from Shopify (limit: {limit})...")
        
        # Fetch from Shopify
        shopify_orders = self.client.get_orders(limit=limit)
        
        print(f"   Fetched {len(shopify_orders)} orders from Shopify")
        
        # Map to internal format
        synced_orders = {}
        for shopify_order in shopify_orders:
            internal_order = self.mapper.map_order(shopify_order)
            order_id = internal_order['order_id']
            synced_orders[order_id] = internal_order
            self.orders_cache[order_id] = internal_order
        
        print(f"✅ Synced {len(synced_orders)} orders")
        
        return synced_orders
    
    def get_order(self, order_id: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get specific order
        
        Args:
            order_id: Order ID or Shopify order number
            force_refresh: Force fetch from Shopify
        
        Returns:
            Order dict or None
        """
        # Check cache first
        if not force_refresh and order_id in self.orders_cache:
            return self.orders_cache[order_id]
        
        # Try to fetch from Shopify
        try:
            # Try as Shopify ID
            shopify_order = self.client.get_order(order_id)
            
            if shopify_order:
                internal_order = self.mapper.map_order(shopify_order)
                self.orders_cache[order_id] = internal_order
                return internal_order
        except Exception as e:
            print(f"Error fetching order {order_id}: {e}")
        
        return None
    
    def search_orders_by_email(self, email: str) -> List[Dict]:
        """
        Search orders by customer email
        
        Args:
            email: Customer email
        
        Returns:
            List of matching orders
        """
        # Fetch recent orders
        orders = self.sync_orders(limit=100)
        
        # Filter by email
        matching = [
            order for order in orders.values()
            if order.get('customer_email', '').lower() == email.lower()
        ]
        
        return matching


# Convenience function
def sync_shopify_orders(brand_name: str = "fashionhub", limit: int = 50) -> Dict:
    """
    Sync orders from Shopify
    
    Args:
        brand_name: Brand name
        limit: Max orders
    
    Returns:
        Synced orders dict
    """
    sync = ShopifyOrderSync(brand_name)
    return sync.sync_orders(limit=limit)
