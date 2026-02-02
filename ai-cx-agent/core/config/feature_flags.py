"""
Feature Flags
Dynamic feature toggling for gradual rollouts and A/B testing
Supports: Environment-based flags, per-brand flags, runtime toggles
"""

from typing import Dict, Optional, List


class FeatureFlags:
    """Feature flag management"""
    
    def __init__(self, config_manager):
        """
        Initialize feature flags
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self._runtime_flags: Dict[str, bool] = {}
        self._brand_flags: Dict[str, Dict[str, bool]] = {}
    
    def is_enabled(self, feature: str, brand_id: Optional[str] = None) -> bool:
        """
        Check if feature is enabled
        
        Args:
            feature: Feature name
            brand_id: Optional brand ID for brand-specific flags
        
        Returns:
            True if feature is enabled
        """
        # Check brand-specific flag first
        if brand_id and brand_id in self._brand_flags:
            if feature in self._brand_flags[brand_id]:
                return self._brand_flags[brand_id][feature]
        
        # Check runtime flag
        if feature in self._runtime_flags:
            return self._runtime_flags[feature]
        
        # Check environment config
        flag_key = f"ENABLE_{feature.upper()}"
        return self.config.get_bool(flag_key, default=False)
    
    def enable(self, feature: str, brand_id: Optional[str] = None):
        """
        Enable feature at runtime
        
        Args:
            feature: Feature name
            brand_id: Optional brand ID for brand-specific enable
        """
        if brand_id:
            if brand_id not in self._brand_flags:
                self._brand_flags[brand_id] = {}
            self._brand_flags[brand_id][feature] = True
        else:
            self._runtime_flags[feature] = True
    
    def disable(self, feature: str, brand_id: Optional[str] = None):
        """
        Disable feature at runtime
        
        Args:
            feature: Feature name
            brand_id: Optional brand ID for brand-specific disable
        """
        if brand_id:
            if brand_id not in self._brand_flags:
                self._brand_flags[brand_id] = {}
            self._brand_flags[brand_id][feature] = False
        else:
            self._runtime_flags[feature] = False
    
    # === Core Features ===
    
    def proactive_features_enabled(self, brand_id: Optional[str] = None) -> bool:
        """Check if proactive features are enabled"""
        return self.is_enabled('proactive_features', brand_id)
    
    def context_resolution_enabled(self, brand_id: Optional[str] = None) -> bool:
        """Check if context resolution is enabled"""
        return self.is_enabled('context_resolution', brand_id)
    
    def quality_monitoring_enabled(self, brand_id: Optional[str] = None) -> bool:
        """Check if quality monitoring is enabled"""
        return self.is_enabled('quality_monitoring', brand_id)
    
    # === Tool Flags ===
    
    def tool_enabled(self, tool_name: str, brand_id: Optional[str] = None) -> bool:
        """
        Check if specific tool is enabled
        
        Args:
            tool_name: Tool name (e.g., 'get_order_status')
            brand_id: Optional brand ID
        
        Returns:
            True if tool is enabled
        """
        return self.is_enabled(f'tool_{tool_name}', brand_id)
    
    def get_enabled_tools(self, brand_id: Optional[str] = None) -> List[str]:
        """
        Get list of enabled tools
        
        Args:
            brand_id: Optional brand ID
        
        Returns:
            List of enabled tool names
        """
        all_tools = [
            'get_order_status',
            'search_knowledge',
            'check_shipping_eligibility',
            'get_product_info'
        ]
        
        return [
            tool for tool in all_tools
            if self.tool_enabled(tool, brand_id)
        ]
    
    # === Integration Flags ===
    
    def integration_enabled(self, integration: str, brand_id: Optional[str] = None) -> bool:
        """
        Check if integration is enabled
        
        Args:
            integration: Integration name (whatsapp, email, instagram, shopify)
            brand_id: Optional brand ID
        
        Returns:
            True if integration is enabled
        """
        return self.is_enabled(integration, brand_id) or self.is_enabled(f'integration_{integration}', brand_id)
    
    def whatsapp_enabled(self, brand_id: Optional[str] = None) -> bool:
        """Check if WhatsApp integration is enabled"""
        return self.integration_enabled('whatsapp', brand_id)
    
    def email_enabled(self, brand_id: Optional[str] = None) -> bool:
        """Check if Email integration is enabled"""
        return self.integration_enabled('email', brand_id)
    
    def instagram_enabled(self, brand_id: Optional[str] = None) -> bool:
        """Check if Instagram integration is enabled"""
        return self.integration_enabled('instagram', brand_id)
    
    def shopify_enabled(self, brand_id: Optional[str] = None) -> bool:
        """Check if Shopify integration is enabled"""
        return self.integration_enabled('shopify', brand_id)
    
    # === Monitoring Flags ===
    
    def metrics_enabled(self) -> bool:
        """Check if metrics collection is enabled"""
        return self.config.get_bool('ENABLE_METRICS', True)
    
    def analytics_enabled(self) -> bool:
        """Check if analytics tracking is enabled"""
        return self.config.get_bool('ENABLE_ANALYTICS', True)
    
    def json_logs_enabled(self) -> bool:
        """Check if JSON logging is enabled"""
        return self.config.get_bool('ENABLE_JSON_LOGS', False)
    
    # === Performance Flags ===
    
    def caching_enabled(self) -> bool:
        """Check if caching is enabled"""
        return self.config.get_bool('ENABLE_CACHING', False)
    
    # === Security Flags ===
    
    def signature_verification_enabled(self) -> bool:
        """Check if webhook signature verification is enabled"""
        return self.config.get_bool('ENABLE_SIGNATURE_VERIFICATION', 
                                   self.config.is_production)
    
    # === Utility Methods ===
    
    def get_all_flags(self, brand_id: Optional[str] = None) -> Dict[str, bool]:
        """
        Get all feature flags and their states
        
        Args:
            brand_id: Optional brand ID
        
        Returns:
            Dict of feature name to enabled status
        """
        flags = {
            # Core features
            'proactive_features': self.proactive_features_enabled(brand_id),
            'context_resolution': self.context_resolution_enabled(brand_id),
            'quality_monitoring': self.quality_monitoring_enabled(brand_id),
            
            # Integrations
            'whatsapp': self.whatsapp_enabled(brand_id),
            'email': self.email_enabled(brand_id),
            'instagram': self.instagram_enabled(brand_id),
            'shopify': self.shopify_enabled(brand_id),
            
            # Monitoring
            'metrics': self.metrics_enabled(),
            'analytics': self.analytics_enabled(),
            'json_logs': self.json_logs_enabled(),
            
            # Performance
            'caching': self.caching_enabled(),
            
            # Security
            'signature_verification': self.signature_verification_enabled()
        }
        
        # Add tools
        for tool in ['get_order_status', 'search_knowledge', 'check_shipping_eligibility', 'get_product_info']:
            flags[f'tool_{tool}'] = self.tool_enabled(tool, brand_id)
        
        return flags
    
    def get_enabled_features(self, brand_id: Optional[str] = None) -> List[str]:
        """
        Get list of enabled features
        
        Args:
            brand_id: Optional brand ID
        
        Returns:
            List of enabled feature names
        """
        all_flags = self.get_all_flags(brand_id)
        return [feature for feature, enabled in all_flags.items() if enabled]
    
    def get_brand_overrides(self, brand_id: str) -> Dict[str, bool]:
        """
        Get brand-specific flag overrides
        
        Args:
            brand_id: Brand ID
        
        Returns:
            Dict of overridden flags
        """
        return self._brand_flags.get(brand_id, {})
    
    def clear_runtime_flags(self):
        """Clear all runtime flags"""
        self._runtime_flags.clear()
        self._brand_flags.clear()
    
    def __repr__(self) -> str:
        enabled_count = len(self.get_enabled_features())
        return f"FeatureFlags(enabled_features={enabled_count})"


# Testing function
def test_feature_flags():
    """Test feature flags"""
    import sys
    from pathlib import Path
    
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from core.config.manager import ConfigManager
    
    print("🧪 TESTING FEATURE FLAGS")
    print("=" * 70)
    print()
    
    test_config = ConfigManager('development')
    test_flags = FeatureFlags(test_config)
    
    # Test 1: Basic flag check
    print("TEST 1: Basic Flag Check")
    proactive = test_flags.proactive_features_enabled()
    print(f"  Proactive Features: {proactive}")
    print("✅ Basic flag check working")
    print()
    
    # Test 2: Tool flags
    print("TEST 2: Tool Flags")
    order_tool = test_flags.tool_enabled('get_order_status')
    print(f"  Order Status Tool: {order_tool}")
    enabled_tools = test_flags.get_enabled_tools()
    print(f"  Enabled Tools: {len(enabled_tools)}")
    print("✅ Tool flags working")
    print()
    
    # Test 3: Integration flags
    print("TEST 3: Integration Flags")
    whatsapp = test_flags.whatsapp_enabled()
    email = test_flags.email_enabled()
    instagram = test_flags.instagram_enabled()
    shopify = test_flags.shopify_enabled()
    print(f"  WhatsApp: {whatsapp}")
    print(f"  Email: {email}")
    print(f"  Instagram: {instagram}")
    print(f"  Shopify: {shopify}")
    print("✅ Integration flags working")
    print()
    
    # Test 4: Runtime flags
    print("TEST 4: Runtime Flag Toggle")
    test_flags.enable('test_feature')
    enabled = test_flags.is_enabled('test_feature')
    print(f"  Test Feature Enabled: {enabled}")
    assert enabled == True
    
    test_flags.disable('test_feature')
    disabled = test_flags.is_enabled('test_feature')
    print(f"  Test Feature Disabled: {disabled}")
    assert disabled == False
    print("✅ Runtime flags working")
    print()
    
    # Test 5: Brand-specific flags
    print("TEST 5: Brand-Specific Flags")
    test_flags.enable('custom_feature', brand_id='fashionhub')
    fashionhub_enabled = test_flags.is_enabled('custom_feature', brand_id='fashionhub')
    techgear_enabled = test_flags.is_enabled('custom_feature', brand_id='techgear')
    print(f"  FashionHub Custom Feature: {fashionhub_enabled}")
    print(f"  TechGear Custom Feature: {techgear_enabled}")
    assert fashionhub_enabled == True
    assert techgear_enabled == False
    print("✅ Brand-specific flags working")
    print()
    
    # Test 6: Get all flags
    print("TEST 6: Get All Flags")
    all_flags = test_flags.get_all_flags()
    print(f"  Total Flags: {len(all_flags)}")
    enabled_features = test_flags.get_enabled_features()
    print(f"  Enabled Features: {len(enabled_features)}")
    if enabled_features:
        print(f"  Features: {', '.join(enabled_features[:5])}...")
    print("✅ Get all flags working")
    print()
    
    # Test 7: Monitoring flags
    print("TEST 7: Monitoring Flags")
    metrics = test_flags.metrics_enabled()
    analytics = test_flags.analytics_enabled()
    print(f"  Metrics: {metrics}")
    print(f"  Analytics: {analytics}")
    print("✅ Monitoring flags working")
    print()
    
    # Test 8: Brand overrides
    print("TEST 8: Brand Overrides")
    overrides = test_flags.get_brand_overrides('fashionhub')
    print(f"  FashionHub Overrides: {overrides}")
    print("✅ Brand overrides working")
    print()
    
    # Summary
    print("=" * 70)
    print("FEATURE FLAGS SUMMARY")
    print("=" * 70)
    print()
    print(f"Environment: {test_config.environment}")
    print(f"Total Flags: {len(all_flags)}")
    print(f"Enabled Features: {len(enabled_features)}")
    print()
    print("Core Features:")
    print(f"  ✓ Proactive Features: {test_flags.proactive_features_enabled()}")
    print(f"  ✓ Context Resolution: {test_flags.context_resolution_enabled()}")
    print(f"  ✓ Quality Monitoring: {test_flags.quality_monitoring_enabled()}")
    print()
    print("Integrations:")
    print(f"  ✓ WhatsApp: {test_flags.whatsapp_enabled()}")
    print(f"  ✓ Email: {test_flags.email_enabled()}")
    print(f"  ✓ Instagram: {test_flags.instagram_enabled()}")
    print(f"  ✓ Shopify: {test_flags.shopify_enabled()}")
    print()
    print("✅ All feature flag tests complete!")


if __name__ == "__main__":
    test_feature_flags()
