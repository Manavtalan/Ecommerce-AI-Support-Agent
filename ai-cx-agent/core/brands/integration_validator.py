"""
Integration Validator
Validates external integrations (Shopify, WhatsApp, etc.)
"""

import os
from typing import Dict, Tuple
from dotenv import load_dotenv

load_dotenv()


class IntegrationValidator:
    """Validates brand integrations"""
    
    @staticmethod
    def validate_shopify(store_url: str, access_token: str = None) -> Tuple[bool, str]:
        """
        Validate Shopify connection
        
        Args:
            store_url: Shopify store URL
            access_token: Shopify access token (optional)
        
        Returns:
            (is_valid, message)
        """
        # Basic format validation
        if not store_url:
            return False, "Store URL is required"
        
        if not store_url.endswith(".myshopify.com"):
            return False, "Store URL must end with .myshopify.com"
        
        # If token provided, test connection
        if access_token:
            try:
                from core.integrations.shopify.client import ShopifyClient
                
                client = ShopifyClient(store_url=store_url, access_token=access_token)
                
                if client.test_connection():
                    return True, "Shopify connection successful"
                else:
                    return False, "Failed to connect to Shopify"
            
            except Exception as e:
                return False, f"Shopify validation error: {str(e)}"
        
        # Format valid but not tested
        return True, "Store URL format valid (not tested)"
    
    @staticmethod
    def validate_whatsapp(api_key: str = None, phone_number: str = None) -> Tuple[bool, str]:
        """
        Validate WhatsApp Business API credentials
        
        Args:
            api_key: WhatsApp API key
            phone_number: Business phone number
        
        Returns:
            (is_valid, message)
        """
        if not phone_number:
            return False, "Phone number is required"
        
        # Basic format validation
        if not phone_number.startswith("+"):
            return False, "Phone number must start with +"
        
        if len(phone_number) < 10:
            return False, "Phone number too short"
        
        # API key validation (if provided)
        if api_key:
            if len(api_key) < 20:
                return False, "API key seems invalid (too short)"
            
            # In production, test actual connection here
            return True, "WhatsApp credentials valid (not tested)"
        
        return True, "Phone number format valid"
    
    @staticmethod
    def validate_email(smtp_host: str = None, smtp_port: int = None) -> Tuple[bool, str]:
        """
        Validate email configuration
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
        
        Returns:
            (is_valid, message)
        """
        if not smtp_host:
            return True, "Email not configured (optional)"
        
        # Basic validation
        if not isinstance(smtp_port, int) or smtp_port <= 0:
            return False, "Invalid SMTP port"
        
        return True, "Email configuration looks valid"
    
    @staticmethod
    def test_api_connection(integration_type: str, credentials: Dict) -> Tuple[bool, str]:
        """
        Test actual API connection
        
        Args:
            integration_type: Type of integration
            credentials: Credentials dict
        
        Returns:
            (success, message)
        """
        if integration_type == "shopify":
            return IntegrationValidator.validate_shopify(
                credentials.get('store_url'),
                credentials.get('access_token')
            )
        
        elif integration_type == "whatsapp":
            return IntegrationValidator.validate_whatsapp(
                credentials.get('api_key'),
                credentials.get('phone_number')
            )
        
        elif integration_type == "email":
            return IntegrationValidator.validate_email(
                credentials.get('smtp_host'),
                credentials.get('smtp_port')
            )
        
        return False, f"Unknown integration type: {integration_type}"
    
    @staticmethod
    def save_credentials_securely(brand_id: str, integration_type: str, credentials: Dict) -> bool:
        """
        Save integration credentials securely
        
        Args:
            brand_id: Brand identifier
            integration_type: Type of integration
            credentials: Credentials to save
        
        Returns:
            True if successful
        """
        # In production, use a secrets manager (AWS Secrets Manager, HashiCorp Vault)
        # For now, warn about storing in .env
        
        print("⚠️  SECURITY WARNING:")
        print("  Credentials should be stored in environment variables or secrets manager")
        print("  Add to .env file:")
        print()
        
        env_prefix = f"{brand_id.upper()}_{integration_type.upper()}"
        
        for key, value in credentials.items():
            env_key = f"{env_prefix}_{key.upper()}"
            print(f"  {env_key}={value}")
        
        print()
        
        return True
    
    @staticmethod
    def validate_all_integrations(brand_config: Dict) -> Dict[str, Tuple[bool, str]]:
        """
        Validate all integrations in brand config
        
        Args:
            brand_config: Brand configuration dict
        
        Returns:
            Dict of integration -> (is_valid, message)
        """
        results = {}
        
        integrations = brand_config.get('integrations', {})
        
        # Shopify
        if integrations.get('shopify', {}).get('enabled'):
            shopify_config = integrations['shopify']
            results['shopify'] = IntegrationValidator.validate_shopify(
                shopify_config.get('store_url')
            )
        
        # WhatsApp
        if integrations.get('whatsapp', {}).get('enabled'):
            whatsapp_config = integrations['whatsapp']
            results['whatsapp'] = IntegrationValidator.validate_whatsapp(
                phone_number=whatsapp_config.get('business_number')
            )
        
        # Email
        if integrations.get('email', {}).get('enabled'):
            email_config = integrations['email']
            results['email'] = IntegrationValidator.validate_email(
                email_config.get('smtp_host')
            )
        
        return results
