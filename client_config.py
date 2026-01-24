# client_config.py
"""
Client Configuration Management
Handles multi-client setup and validation.
"""

import json
import os
from typing import Dict, Any


class ClientConfig:
    """Manages individual client configurations"""
    
    TEMPLATE = {
        "client_info": {
            "client_id": "",
            "client_name": "",
            "industry": "",
            "support_email": ""
        },
        "integrations": {
            "shopify": {
                "enabled": False,
                "shop_name": ""
            }
        },
        "brand_voice": {
            "template": "startup_cool"
        },
        "business_rules": {
            "escalate_on": ["cancellation", "refund_request"],
            "auto_respond_to": ["order_status", "shipping"]
        },
        "features_enabled": {
            "order_status": True,
            "returns_info": False
        }
    }
    
    def __init__(self, config_path: str = None):
        """Load client config from file or use defaults"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self.TEMPLATE.copy()
    
    def get(self, key: str, default=None):
        """Get nested config value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        
        return value
    
    def validate(self) -> tuple[bool, list]:
        """
        Validate required fields are present.
        Returns (is_valid, errors)
        """
        errors = []
        
        required_fields = [
            "client_info.client_name",
            "brand_voice.template"
        ]
        
        for field in required_fields:
            value = self.get(field)
            if not value:
                errors.append(f"Missing required field: {field}")
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def create_template(output_path: str):
        """Create a new client config template"""
        with open(output_path, 'w') as f:
            json.dump(ClientConfig.TEMPLATE, f, indent=2)
        print(f"✅ Created template at: {output_path}")


# Example usage:
# config = ClientConfig("clients/fashionhub/config.json")
# brand_template = config.get("brand_voice.template")