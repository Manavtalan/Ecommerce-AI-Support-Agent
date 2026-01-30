"""
Shopify API Client
Production-grade wrapper for Shopify Admin API
"""

import os
import time
import shopify
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class ShopifyClient:
    """
    Shopify API client with error handling and rate limiting
    """
    
    def __init__(
        self,
        store_url: Optional[str] = None,
        access_token: Optional[str] = None,
        api_version: Optional[str] = None
    ):
        """
        Initialize Shopify client
        
        Args:
            store_url: Shopify store URL (e.g., 'store.myshopify.com')
            access_token: Admin API access token
            api_version: API version (e.g., '2024-01')
        """
        self.store_url = store_url or os.getenv("SHOPIFY_STORE_URL")
        self.access_token = access_token or os.getenv("SHOPIFY_ACCESS_TOKEN")
        self.api_version = api_version or os.getenv("SHOPIFY_API_VERSION", "2024-01")
        
        if not self.store_url or not self.access_token:
            raise ValueError("Shopify credentials not provided")
        
        # Initialize session
        self.session = self._create_session()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests
    
    def _create_session(self) -> shopify.Session:
        """Create Shopify API session"""
        session = shopify.Session(
            self.store_url,
            self.api_version,
            self.access_token
        )
        shopify.ShopifyResource.activate_session(session)
        return session
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """
        Get order by ID
        
        Args:
            order_id: Shopify order ID
        
        Returns:
            Order dict or None if not found
        """
        self._rate_limit()
        
        try:
            order = shopify.Order.find(order_id)
            return self._order_to_dict(order)
        except Exception as e:
            print(f"Error fetching order {order_id}: {e}")
            return None
    
    def get_orders(
        self,
        status: str = "any",
        limit: int = 50,
        since_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get orders list
        
        Args:
            status: Order status filter ('open', 'closed', 'any')
            limit: Max orders to return (1-250)
            since_id: Get orders after this ID
        
        Returns:
            List of order dicts
        """
        self._rate_limit()
        
        try:
            params = {"status": status, "limit": min(limit, 250)}
            if since_id:
                params["since_id"] = since_id
            
            orders = shopify.Order.find(**params)
            return [self._order_to_dict(order) for order in orders]
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return []
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """
        Get product by ID
        
        Args:
            product_id: Shopify product ID
        
        Returns:
            Product dict or None
        """
        self._rate_limit()
        
        try:
            product = shopify.Product.find(product_id)
            return self._product_to_dict(product)
        except Exception as e:
            print(f"Error fetching product {product_id}: {e}")
            return None
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """
        Get customer by ID
        
        Args:
            customer_id: Shopify customer ID
        
        Returns:
            Customer dict or None
        """
        self._rate_limit()
        
        try:
            customer = shopify.Customer.find(customer_id)
            return self._customer_to_dict(customer)
        except Exception as e:
            print(f"Error fetching customer {customer_id}: {e}")
            return None
    
    def _order_to_dict(self, order) -> Dict:
        """Convert Shopify order object to dict"""
        return {
            "id": str(order.id),
            "order_number": order.order_number,
            "name": order.name,
            "email": order.email,
            "created_at": str(order.created_at),
            "updated_at": str(order.updated_at),
            "cancelled_at": str(order.cancelled_at) if order.cancelled_at else None,
            "closed_at": str(order.closed_at) if order.closed_at else None,
            "financial_status": order.financial_status,
            "fulfillment_status": order.fulfillment_status,
            "total_price": float(order.total_price),
            "subtotal_price": float(order.subtotal_price),
            "total_tax": float(order.total_tax),
            "currency": order.currency,
            "customer": {
                "id": str(order.customer.id) if order.customer else None,
                "email": order.customer.email if order.customer else order.email,
                "first_name": order.customer.first_name if order.customer else None,
                "last_name": order.customer.last_name if order.customer else None,
            },
            "shipping_address": {
                "address1": order.shipping_address.address1 if order.shipping_address else None,
                "city": order.shipping_address.city if order.shipping_address else None,
                "province": order.shipping_address.province if order.shipping_address else None,
                "country": order.shipping_address.country if order.shipping_address else None,
                "zip": order.shipping_address.zip if order.shipping_address else None,
            } if order.shipping_address else None,
            "line_items": [
                {
                    "id": str(item.id),
                    "product_id": str(item.product_id) if item.product_id else None,
                    "variant_id": str(item.variant_id) if item.variant_id else None,
                    "title": item.title,
                    "quantity": item.quantity,
                    "price": float(item.price),
                } for item in order.line_items
            ] if order.line_items else [],
            "fulfillments": [
                {
                    "id": str(f.id),
                    "status": f.status,
                    "tracking_company": f.tracking_company,
                    "tracking_number": f.tracking_number,
                    "tracking_url": f.tracking_url,
                } for f in order.fulfillments
            ] if hasattr(order, 'fulfillments') and order.fulfillments else []
        }
    
    def _product_to_dict(self, product) -> Dict:
        """Convert Shopify product to dict"""
        return {
            "id": str(product.id),
            "title": product.title,
            "vendor": product.vendor,
            "product_type": product.product_type,
            "created_at": str(product.created_at),
            "updated_at": str(product.updated_at),
            "published_at": str(product.published_at) if product.published_at else None,
            "status": product.status,
            "variants": [
                {
                    "id": str(v.id),
                    "title": v.title,
                    "price": float(v.price),
                    "sku": v.sku,
                    "inventory_quantity": v.inventory_quantity,
                } for v in product.variants
            ] if product.variants else []
        }
    
    def _customer_to_dict(self, customer) -> Dict:
        """Convert Shopify customer to dict"""
        return {
            "id": str(customer.id),
            "email": customer.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "phone": customer.phone,
            "created_at": str(customer.created_at),
            "updated_at": str(customer.updated_at),
            "orders_count": customer.orders_count,
            "total_spent": float(customer.total_spent) if customer.total_spent else 0.0,
        }
    
    def test_connection(self) -> bool:
        """Test Shopify connection"""
        try:
            shopify.Shop.current()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def __repr__(self) -> str:
        return f"ShopifyClient(store={self.store_url}, api_version={self.api_version})"


# Factory function
def create_shopify_client(
    store_url: Optional[str] = None,
    access_token: Optional[str] = None
) -> ShopifyClient:
    """
    Create Shopify client
    
    Args:
        store_url: Store URL (optional, uses env)
        access_token: Access token (optional, uses env)
    
    Returns:
        ShopifyClient instance
    """
    return ShopifyClient(store_url=store_url, access_token=access_token)
