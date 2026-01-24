# brand_voice.py
"""
Brand Voice Configuration System
Allows multiple clients with different personalities using same codebase.
"""

import json
from typing import Dict, Any
import os


class BrandVoice:
    """Manages brand-specific messaging and tone"""
    
    TEMPLATES = {
        "startup_cool": {
            "tone": "casual",
            "use_emojis": True,
            "emoji_set": ["🎉", "✨", "🚚", "📦", "👋"],
            "greeting": "Hey there! 👋",
            "order_found": "Great news!",
            "order_shipped": "Your order is on its way! 🚚",
            "escalation": "Let me connect you with our team!",
            "closing": "Anything else I can help with?",
            "forbidden_words": []
        },
        
        "premium_luxury": {
            "tone": "professional",
            "use_emojis": False,
            "emoji_set": [],
            "greeting": "Good day.",
            "order_found": "I have located your order.",
            "order_shipped": "Your order has been dispatched via our premium courier service.",
            "escalation": "Allow me to connect you with our support specialists.",
            "closing": "Is there anything else I may assist you with?",
            "forbidden_words": ["hey", "cool", "awesome"]
        },
        
        "minimalist": {
            "tone": "direct",
            "use_emojis": False,
            "emoji_set": [],
            "greeting": "Hello.",
            "order_found": "Order found.",
            "order_shipped": "Order shipped.",
            "escalation": "Forwarding to support.",
            "closing": "Anything else?",
            "forbidden_words": []
        }
    }
    
    def __init__(self, template_name: str = "startup_cool"):
        """Initialize with a brand template"""
        if template_name in self.TEMPLATES:
            self.config = self.TEMPLATES[template_name].copy()
        else:
            self.config = self.TEMPLATES["startup_cool"].copy()
        
        self.template_name = template_name
    
    @classmethod
    def from_file(cls, config_path: str):
        """Load brand config from JSON file"""
        with open(config_path, 'r') as f:
            custom_config = json.load(f)
        
        instance = cls()
        instance.config.update(custom_config.get("brand_voice", {}))
        return instance
    
    def format_response(self, response_type: str, **kwargs) -> str:
        """
        Format a response according to brand voice.
        
        Usage:
            brand.format_response("order_shipped", order_id="12345")
        """
        template = self.config.get(response_type, "")
        
        # Simple variable substitution
        for key, value in kwargs.items():
            template = template.replace(f"{{{key}}}", str(value))
        
        return template
    
    def get_closing(self, turn_number: int = 0) -> str:
        """Get brand-appropriate closing message"""
        return self.config.get("closing", "Anything else I can help you with?")
    
    def should_use_emoji(self) -> bool:
        """Check if emojis should be used"""
        return self.config.get("use_emojis", False)


# Example usage in your code:
# brand = BrandVoice("premium_luxury")
# closing = brand.get_closing()