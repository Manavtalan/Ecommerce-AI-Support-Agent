# response_templates.py
"""
Human-like Response Templates
Deterministic, reassuring, professional responses.
"""

from typing import Dict, Any


class ResponseTemplates:
    """
    Generates human-like responses based on order state.
    NO AI, NO hallucination, pure template logic.
    """
    
    @staticmethod
    def format_order_status_response(
        order_id: str,
        order_data: Dict[str, Any],
        is_followup: bool = False
    ) -> str:
        """
        Generate reassuring, human-like order status response.
        """
        status = order_data['status'].lower()
        
        if is_followup:
            return ResponseTemplates._format_followup_response(order_id, order_data, status)
        else:
            return ResponseTemplates._format_first_mention_response(order_id, order_data, status)
    
    @staticmethod
    def _format_followup_response(order_id: str, order_data: Dict, status: str) -> str:
        """Conversational follow-up response."""
        
        if status == "shipped":
            response = (
                f"Your order #{order_id} is on its way and tracking looks good! "
                f"It should reach you by {order_data.get('estimated_delivery', 'soon')}."
            )
            if order_data.get('tracking_url'):
                response += f"\n\nYou can track it here: {order_data['tracking_url']}"
            response += "\n\nDelivery times can vary slightly, but everything's on track."
            
        elif status == "processing":
            response = (
                f"Your order #{order_id} is being prepared by our warehouse team. "
                f"It typically ships within 1-2 business days. "
                f"You'll get a tracking number as soon as it ships!"
            )
            
        elif status == "delivered":
            response = (
                f"Good news! Your order #{order_id} was delivered successfully. "
                f"If you haven't received it yet, please check with your building reception or neighbors."
            )
            
        else:
            response = f"Your order #{order_id} is currently {status}."
        
        return response
    
    @staticmethod
    def _format_first_mention_response(order_id: str, order_data: Dict, status: str) -> str:
        """Professional first-time response."""
        
        lines = []
        
        if status == "shipped":
            lines.append(f"✓ Your order #{order_id} has been shipped!")
        elif status == "processing":
            lines.append(f"✓ Your order #{order_id} is being prepared.")
        elif status == "delivered":
            lines.append(f"✓ Your order #{order_id} has been delivered!")
        else:
            lines.append(f"✓ Your order #{order_id} status: {status}")
        
        if order_data.get("courier"):
            lines.append(f"  Courier: {order_data['courier']}")
        
        if order_data.get("tracking_url"):
            lines.append(f"  Track here: {order_data['tracking_url']}")
        
        if order_data.get("estimated_delivery"):
            lines.append(f"  Expected delivery: {order_data['estimated_delivery']}")
        
        return "\n".join(lines)
    
    @staticmethod
    def get_dynamic_closing(context) -> str:
        """
        Generate contextual closing message.
        Avoids repetitive "Anything else I can help you with?"
        """
        
        closings = [
            "Is there anything else you'd like to know?",
            "Would you like help with anything else?",
            "Can I help you with another order?",
            "Need any other information?",
            "Anything else I can assist with?"
        ]
        
        # Rotate based on conversation turn
        index = context.conversation_turns % len(closings)
        return closings[index]