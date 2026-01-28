"""
Brand Configuration Loader
Loads brand-specific configuration from YAML and JSON files
"""

import os
import json
import yaml
from typing import Dict, Optional, List
from pathlib import Path


class BrandLoader:
    """
    Loads and manages brand-specific configuration
    """
    
    def __init__(self, brand_name: str = "fashionhub"):
        """
        Initialize brand loader
        
        Args:
            brand_name: Name of the brand to load
        """
        self.brand_name = brand_name
        self.base_path = Path("test_data")
        
        # Loaded data
        self.brand_config: Optional[Dict] = None
        self.voice_guidelines: Optional[Dict] = None
        self.orders: Optional[Dict] = None
        self.products: Optional[Dict] = None
        
        # Load all data
        self._load_all()
    
    def _load_all(self) -> None:
        """Load all brand data"""
        self.brand_config = self._load_brand_config()
        self.voice_guidelines = self._load_voice_guidelines()
        self.orders = self._load_orders()
        self.products = self._load_products()
    
    def _load_brand_config(self) -> Dict:
        """Load brand_config.yaml"""
        config_path = self.base_path / "brands" / self.brand_name / "brand_config.yaml"
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"⚠️  Warning: {config_path} not found")
            return {}
        except Exception as e:
            print(f"⚠️  Error loading brand config: {e}")
            return {}
    
    def _load_voice_guidelines(self) -> Dict:
        """Load voice_guidelines.yaml"""
        voice_path = self.base_path / "brands" / self.brand_name / "voice_guidelines.yaml"
        
        try:
            with open(voice_path, 'r') as f:
                guidelines = yaml.safe_load(f)
            return guidelines
        except FileNotFoundError:
            print(f"⚠️  Warning: {voice_path} not found")
            return {}
        except Exception as e:
            print(f"⚠️  Error loading voice guidelines: {e}")
            return {}
    
    def _load_orders(self) -> Dict:
        """Load fashionhub_orders.json"""
        orders_path = self.base_path / "orders" / f"{self.brand_name}_orders.json"
        
        try:
            with open(orders_path, 'r') as f:
                orders = json.load(f)
            return orders
        except FileNotFoundError:
            print(f"⚠️  Warning: {orders_path} not found")
            return {}
        except Exception as e:
            print(f"⚠️  Error loading orders: {e}")
            return {}
    
    def _load_products(self) -> Dict:
        """Load fashionhub_products.json"""
        products_path = self.base_path / "products" / f"{self.brand_name}_products.json"
        
        try:
            with open(products_path, 'r') as f:
                products = json.load(f)
            return products
        except FileNotFoundError:
            print(f"⚠️  Warning: {products_path} not found")
            return {}
        except Exception as e:
            print(f"⚠️  Error loading products: {e}")
            return {}
    
    # Brand Config Helpers
    
    def get_brand_name(self) -> str:
        """Get brand display name"""
        return self.brand_config.get("name", self.brand_name.title())
    
    def get_return_window(self) -> int:
        """Get return window in days"""
        return self.brand_config.get("return_window_days", 30)
    
    def get_free_shipping_threshold(self) -> int:
        """Get free shipping threshold"""
        return self.brand_config.get("free_shipping_threshold", 999)
    
    def get_support_email(self) -> str:
        """Get support email"""
        return self.brand_config.get("support_email", "support@example.com")
    
    def get_support_phone(self) -> str:
        """Get support phone"""
        return self.brand_config.get("support_phone", "")
    
    # Voice Guidelines Helpers
    
    def get_brand_voice(self) -> Dict:
        """Get complete brand voice configuration"""
        return {
            "tone": self.voice_guidelines.get("tone", "friendly_professional"),
            "formality": self.voice_guidelines.get("formality", "casual"),
            "forbidden_phrases": self.voice_guidelines.get("forbidden_phrases", []),
            "signature_phrases": self.voice_guidelines.get("signature_phrases", []),
            "emoji_usage": self.voice_guidelines.get("emoji_usage", "moderate")
        }
    
    def get_forbidden_phrases(self) -> List[str]:
        """Get list of forbidden phrases"""
        return self.voice_guidelines.get("forbidden_phrases", [])
    
    def get_signature_phrases(self) -> List[str]:
        """Get list of signature phrases"""
        signature = self.voice_guidelines.get("signature_phrases", [])
        # Handle if it's a dict (extract values) or list
        if isinstance(signature, dict):
            return list(signature.values())
        elif isinstance(signature, list):
            return signature
        else:
            return []
    
    # Order Helpers
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """
        Get order by ID
        
        Args:
            order_id: Order ID to lookup
        
        Returns:
            Order dict or None if not found
        """
        return self.orders.get(order_id)
    
    def get_order_status(self, order_id: str) -> Optional[str]:
        """Get order status"""
        order = self.get_order(order_id)
        return order.get("status") if order else None
    
    def get_order_facts(self, order_id: str) -> Dict:
        """
        Get order facts formatted for LLM composer
        
        Args:
            order_id: Order ID
        
        Returns:
            Dictionary of facts about the order
        """
        order = self.get_order(order_id)
        
        if not order:
            return {"error": f"Order {order_id} not found"}
        
        facts = {
            "order_id": order_id,
            "status": order.get("status", "unknown"),
            "order_date": order.get("order_date", ""),
            "total": order.get("total_amount", 0),
            "payment_method": order.get("payment_method", ""),
        }
        
        # Add shipping info if available
        if "shipping" in order:
            shipping = order["shipping"]
            facts["courier"] = shipping.get("courier", "")
            facts["tracking_number"] = shipping.get("tracking_number", "")
            facts["tracking_url"] = shipping.get("tracking_url", "")
            facts["estimated_delivery"] = shipping.get("estimated_delivery", "")
            facts["current_location"] = shipping.get("current_location", "")
            
            # Add delay info if present
            if shipping.get("delay_reason"):
                facts["status"] = "delayed"
                facts["delay_reason"] = shipping["delay_reason"]
                facts["revised_eta"] = shipping.get("revised_eta", "")
        
        # Add items info
        if "items" in order:
            items = order["items"]
            facts["items_count"] = len(items)
            facts["items"] = ", ".join([item["name"] for item in items])
        
        return facts
    
    # Product Helpers
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get product by ID"""
        return self.products.get(product_id)
    
    def get_product_name(self, product_id: str) -> str:
        """Get product name"""
        product = self.get_product(product_id)
        return product.get("name", "Unknown Product") if product else "Unknown Product"
    
    # System Prompt Generator
    
    def get_system_prompt(self) -> str:
        """
        Generate system prompt for LLM based on brand configuration
        
        Returns:
            Complete system prompt string
        """
        brand_name = self.get_brand_name()
        tone = self.voice_guidelines.get("tone", "friendly_professional")
        formality = self.voice_guidelines.get("formality", "casual")
        
        prompt = f"""You are a customer support agent for {brand_name}.

Your Communication Style:
- Tone: {tone}
- Formality: {formality}
- Be empathetic, helpful, and natural

Key Brand Information:
- Return window: {self.get_return_window()} days
- Free shipping: Orders above ₹{self.get_free_shipping_threshold()}
- Support: {self.get_support_email()}

Important Rules:
- ONLY use facts provided to you
- NEVER make up order numbers, tracking info, or dates
- If you don't have information, say so honestly
- Show empathy for frustrated customers
"""
        
        # Add forbidden phrases
        forbidden = self.get_forbidden_phrases()
        if forbidden:
            prompt += f"\n\nNEVER use these phrases:\n"
            for phrase in forbidden[:5]:  # Show first 5
                prompt += f"- {phrase}\n"
        
        return prompt
    
    def __repr__(self) -> str:
        """String representation"""
        return f"BrandLoader(brand={self.brand_name}, orders={len(self.orders)}, products={len(self.products)})"


# Factory function
def load_brand(brand_name: str = "fashionhub") -> BrandLoader:
    """
    Load brand configuration
    
    Args:
        brand_name: Brand to load
    
    Returns:
        BrandLoader instance
    """
    return BrandLoader(brand_name=brand_name)
