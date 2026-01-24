# response_formatter.py
"""
Professional Response Formatter
Works with brand voice to generate human-like responses.
"""

from typing import Dict, Any
from brand_voice import BrandVoice


class ResponseFormatter:
    """Formats responses with brand voice and reassurance"""
    
    def __init__(self, brand_voice: BrandVoice = None):
        self.brand = brand_voice or BrandVoice("startup_cool")
    
    def format_order_status(
        self, 
        order_id: str, 
        order_data: Dict[str, Any], 
        is_followup: bool = False
    ) -> str:
        """
        Generate order status response with brand voice.
        Replaces your respond_with_order_status function.
        """
        status = order_data['status'].lower()
        lines = []
        
        if is_followup:
            # Conversational follow-up
            if status == "shipped":
                msg = f"Your order #{order_id} is on its way! Should reach you by {order_data.get('estimated_delivery', 'soon')}."
            elif status == "processing":
                msg = f"Your order #{order_id} is being prepared. It should ship within 1-2 business days."
            elif status == "delivered":
                msg = f"Good news! Your order #{order_id} was already delivered."
            else:
                msg = f"Your order #{order_id} is currently {status}."
            
            if self.brand.should_use_emoji():
                msg += " 📦"
            
            lines.append(msg)
        else:
            # First mention
            prefix = "✓ " if not self.brand.should_use_emoji() else "✅ "
            
            if status == "shipped":
                lines.append(f"{prefix}Your order #{order_id} has been shipped!")
            elif status == "processing":
                lines.append(f"{prefix}Your order #{order_id} is being prepared.")
            elif status == "delivered":
                lines.append(f"{prefix}Your order #{order_id} has been delivered!")
            else:
                lines.append(f"{prefix}Your order #{order_id} status: {status}")
        
        # Add details
        if order_data.get("courier"):
            lines.append(f"  Courier: {order_data['courier']}")
        if order_data.get("tracking_url"):
            lines.append(f"  Track here: {order_data['tracking_url']}")
        if order_data.get("estimated_delivery"):
            lines.append(f"  Expected delivery: {order_data['estimated_delivery']}")
        
        # Add closing
        lines.append("")
        lines.append(self.brand.get_closing())
        
        return "\n".join(lines)
    
    def format_escalation(self) -> str:
        """Brand-specific escalation message"""
        return self.brand.format_response("escalation")
    
    def format_greeting(self) -> str:
        """Brand-specific greeting"""
        return self.brand.format_response("greeting")