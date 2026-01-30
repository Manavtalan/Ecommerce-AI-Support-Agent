"""
Shopify Schema Mapper
Maps Shopify order format to internal order format
"""

from typing import Dict, Optional
from datetime import datetime


class ShopifyOrderMapper:
    """Maps Shopify orders to internal format"""
    
    @staticmethod
    def map_order(shopify_order: Dict) -> Dict:
        """
        Map Shopify order to internal format
        
        Args:
            shopify_order: Order dict from ShopifyClient
        
        Returns:
            Order in internal format (matching fashionhub_orders.json)
        """
        # Extract basic info
        order_id = str(shopify_order.get('order_number', shopify_order.get('id')))
        
        # Map fulfillment status to internal status
        fulfillment_status = shopify_order.get('fulfillment_status')
        status = ShopifyOrderMapper._map_status(fulfillment_status)
        
        # Extract customer info
        customer = shopify_order.get('customer', {})
        email = customer.get('email') or shopify_order.get('email', '')
        customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        if not customer_name:
            customer_name = email.split('@')[0] if email else 'Customer'
        
        # Extract shipping info
        shipping_address = shopify_order.get('shipping_address') or {}
        
        # Extract fulfillment/tracking info
        fulfillments = shopify_order.get('fulfillments', [])
        tracking_info = ShopifyOrderMapper._extract_tracking(fulfillments)
        
        # Map line items to products
        line_items = shopify_order.get('line_items', [])
        items = ShopifyOrderMapper._map_line_items(line_items)
        
        # Build internal order format
        internal_order = {
            "order_id": order_id,
            "order_date": shopify_order.get('created_at', datetime.now().isoformat()),
            "customer_name": customer_name,
            "customer_email": email,
            "customer_phone": customer.get('phone', ''),
            "status": status,
            "payment_method": ShopifyOrderMapper._map_payment_method(
                shopify_order.get('financial_status')
            ),
            "total_amount": float(shopify_order.get('total_price', 0)),
            "items": items,
            "shipping": {
                "address": {
                    "line1": shipping_address.get('address1', ''),
                    "city": shipping_address.get('city', ''),
                    "state": shipping_address.get('province', ''),
                    "pincode": shipping_address.get('zip', ''),
                    "country": shipping_address.get('country', 'India')
                },
                "courier": tracking_info.get('courier', 'Standard Shipping'),
                "tracking_number": tracking_info.get('tracking_number', ''),
                "tracking_url": tracking_info.get('tracking_url', ''),
                "estimated_delivery": tracking_info.get('estimated_delivery', ''),
                "current_location": tracking_info.get('current_location', ''),
                "shipped_date": tracking_info.get('shipped_date', '')
            },
            "shopify_data": {
                "shopify_id": shopify_order.get('id'),
                "shopify_order_number": shopify_order.get('order_number'),
                "fulfillment_status": fulfillment_status,
                "financial_status": shopify_order.get('financial_status'),
                "updated_at": shopify_order.get('updated_at')
            }
        }
        
        return internal_order
    
    @staticmethod
    def _map_status(fulfillment_status: Optional[str]) -> str:
        """Map Shopify fulfillment status to internal status"""
        status_map = {
            None: 'processing',
            'fulfilled': 'delivered',
            'partial': 'shipped',
            'restocked': 'cancelled',
            'pending': 'processing',
            'open': 'processing'
        }
        return status_map.get(fulfillment_status, 'processing')
    
    @staticmethod
    def _map_payment_method(financial_status: Optional[str]) -> str:
        """Map financial status to payment method"""
        if financial_status in ['paid', 'authorized']:
            return 'paid_online'
        elif financial_status == 'pending':
            return 'cod'
        return 'unknown'
    
    @staticmethod
    def _extract_tracking(fulfillments: list) -> Dict:
        """Extract tracking info from fulfillments"""
        if not fulfillments:
            return {}
        
        # Get most recent fulfillment
        fulfillment = fulfillments[-1]
        
        return {
            "courier": fulfillment.get('tracking_company', 'Standard Shipping'),
            "tracking_number": fulfillment.get('tracking_number', ''),
            "tracking_url": fulfillment.get('tracking_url', ''),
            "shipped_date": '',  # Would need to parse from fulfillment
            "current_location": '',  # Not available from Shopify
            "estimated_delivery": ''  # Not available from Shopify
        }
    
    @staticmethod
    def _map_line_items(line_items: list) -> list:
        """Map Shopify line items to internal items format"""
        items = []
        
        for item in line_items:
            items.append({
                "product_id": str(item.get('product_id', '')),
                "name": item.get('title', 'Product'),
                "quantity": item.get('quantity', 1),
                "price": float(item.get('price', 0)),
                "size": '',  # Not directly available
                "color": ''  # Not directly available
            })
        
        return items


# Convenience function
def map_shopify_order(shopify_order: Dict) -> Dict:
    """
    Map a Shopify order to internal format
    
    Args:
        shopify_order: Shopify order dict
    
    Returns:
        Internal format order dict
    """
    return ShopifyOrderMapper.map_order(shopify_order)
