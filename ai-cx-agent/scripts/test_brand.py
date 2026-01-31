#!/usr/bin/env python3
"""
Brand Test Suite
Comprehensive testing for newly onboarded brands
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.brands.registry import get_brand_registry
from core.brands.session import create_brand_session
from core.brands.voice import BrandVoice
from core.brands.policy_uploader import PolicyUploader
from core.orchestrator import ConversationOrchestrator


class BrandTester:
    """Comprehensive brand testing"""
    
    def __init__(self, brand_id: str):
        """
        Initialize tester
        
        Args:
            brand_id: Brand to test
        """
        self.brand_id = brand_id
        self.registry = get_brand_registry()
        
        if not self.registry.validate_brand_id(brand_id):
            raise ValueError(f"Brand {brand_id} not found")
        
        self.brand_config = self.registry.get_brand_by_id(brand_id)
        self.passed = 0
        self.failed = 0
    
    def print_test(self, test_name: str):
        """Print test header"""
        print(f"\n{'─' * 70}")
        print(f"TEST: {test_name}")
        print(f"{'─' * 70}")
    
    def assert_test(self, condition: bool, message: str):
        """Assert a test condition"""
        if condition:
            print(f"  ✅ {message}")
            self.passed += 1
        else:
            print(f"  ❌ {message}")
            self.failed += 1
    
    def test_brand_registration(self) -> bool:
        """Test 1: Brand Registration"""
        self.print_test("Brand Registration")
        
        # Check brand exists
        exists = self.registry.validate_brand_id(self.brand_id)
        self.assert_test(exists, "Brand exists in registry")
        
        # Check brand config loaded
        config_loaded = self.brand_config is not None
        self.assert_test(config_loaded, "Brand config loaded")
        
        # Check required fields
        has_name = bool(self.brand_config.get('name'))
        self.assert_test(has_name, "Brand has name")
        
        has_industry = bool(self.brand_config.get('industry'))
        self.assert_test(has_industry, "Brand has industry")
        
        return exists and config_loaded
    
    def test_brand_voice(self) -> bool:
        """Test 2: Brand Voice Configuration"""
        self.print_test("Brand Voice Configuration")
        
        try:
            voice = BrandVoice(self.brand_id)
            
            # Test voice loading
            self.assert_test(True, "Voice config loaded")
            
            # Test tone
            tone = voice.get_tone()
            self.assert_test(bool(tone), f"Has tone: {tone}")
            
            # Test formality
            formality = voice.get_formality()
            self.assert_test(bool(formality), f"Has formality: {formality}")
            
            # Test emoji usage
            emoji = voice.get_emoji_usage()
            self.assert_test(bool(emoji), f"Has emoji setting: {emoji}")
            
            # Test tone description
            tone_desc = voice.get_tone_description()
            self.assert_test(len(tone_desc) > 20, "Tone description generated")
            
            # Test voice guidelines
            guidelines = voice.get_voice_guidelines()
            self.assert_test(len(guidelines) > 10, "Voice guidelines generated")
            
            return True
        
        except Exception as e:
            self.assert_test(False, f"Voice loading failed: {e}")
            return False
    
    def test_session_creation(self) -> bool:
        """Test 3: Session Management"""
        self.print_test("Session Management")
        
        try:
            session = create_brand_session(self.brand_id)
            
            # Test session created
            self.assert_test(True, "Session created")
            
            # Test brand scope
            scope = session.get_brand_scope()
            self.assert_test(
                scope.get('brand_id') == self.brand_id,
                f"Brand scope correct: {scope}"
            )
            
            # Test voice config access
            voice_config = session.get_voice_config()
            self.assert_test(
                isinstance(voice_config, dict),
                "Voice config accessible"
            )
            
            # Test policies access
            policies = session.get_policies()
            self.assert_test(
                isinstance(policies, dict),
                "Policies accessible"
            )
            
            return True
        
        except Exception as e:
            self.assert_test(False, f"Session creation failed: {e}")
            return False
    
    def test_policy_retrieval(self) -> bool:
        """Test 4: Policy Retrieval"""
        self.print_test("Policy Retrieval (RAG)")
        
        try:
            uploader = PolicyUploader(self.brand_id)
            
            # Check policy files
            policy_files = uploader.get_policy_files()
            self.assert_test(
                len(policy_files) > 0,
                f"Policy files found: {len(policy_files)}"
            )
            
            # Check coverage
            coverage = uploader.validate_policy_coverage()
            total_policies = len(coverage)
            present_policies = sum(1 for exists in coverage.values() if exists)
            
            self.assert_test(
                present_policies > 0,
                f"Policies present: {present_policies}/{total_policies}"
            )
            
            # Test RAG availability
            try:
                from core.rag.retriever import KnowledgeRetriever
                retriever = KnowledgeRetriever(self.brand_id)
                self.assert_test(True, "RAG retriever initialized")
            except Exception as e:
                self.assert_test(False, f"RAG not available: {e}")
            
            return len(policy_files) > 0
        
        except Exception as e:
            self.assert_test(False, f"Policy retrieval failed: {e}")
            return False
    
    def test_data_isolation(self) -> bool:
        """Test 5: Data Isolation"""
        self.print_test("Data Isolation")
        
        try:
            session = create_brand_session(self.brand_id)
            
            # Test cross-brand access prevention
            fake_resource = {"brand_id": "different_brand", "data": "test"}
            
            try:
                session.validate_access(fake_resource)
                self.assert_test(False, "Cross-brand access NOT blocked (security issue!)")
                return False
            except PermissionError:
                self.assert_test(True, "Cross-brand access blocked correctly")
            
            # Test own brand access
            own_resource = {"brand_id": self.brand_id, "data": "test"}
            try:
                session.validate_access(own_resource)
                self.assert_test(True, "Own brand access allowed")
            except PermissionError:
                self.assert_test(False, "Own brand access blocked (should allow!)")
                return False
            
            return True
        
        except Exception as e:
            self.assert_test(False, f"Data isolation test failed: {e}")
            return False
    
    def test_orchestrator(self) -> bool:
        """Test 6: Orchestrator Integration"""
        self.print_test("Orchestrator Integration")
        
        try:
            orch = ConversationOrchestrator(brand_id=self.brand_id)
            
            self.assert_test(True, "Orchestrator created")
            self.assert_test(
                orch.brand_id == self.brand_id,
                f"Orchestrator has correct brand: {orch.brand_id}"
            )
            
            # Test simple conversation
            response, metadata = orch.process_message("Hello!")
            
            self.assert_test(
                len(response) > 0,
                f"Response generated: {len(response)} chars"
            )
            
            self.assert_test(
                metadata['brand_id'] == self.brand_id,
                "Response metadata correct"
            )
            
            return True
        
        except Exception as e:
            self.assert_test(False, f"Orchestrator test failed: {e}")
            return False
    
    def test_integration_config(self) -> bool:
        """Test 7: Integration Configuration"""
        self.print_test("Integration Configuration")
        
        integrations = self.brand_config.get('integrations', {})
        
        # Shopify
        shopify = integrations.get('shopify', {})
        if shopify.get('enabled'):
            has_url = bool(shopify.get('store_url'))
            self.assert_test(has_url, f"Shopify configured: {shopify.get('store_url')}")
        else:
            self.assert_test(True, "Shopify not enabled (OK)")
        
        # WhatsApp
        whatsapp = integrations.get('whatsapp', {})
        if whatsapp.get('enabled'):
            has_number = bool(whatsapp.get('business_number'))
            self.assert_test(has_number, "WhatsApp configured")
        else:
            self.assert_test(True, "WhatsApp not enabled (OK)")
        
        return True
    
    def test_response_quality(self) -> bool:
        """Test 8: Response Quality"""
        self.print_test("Response Quality")
        
        try:
            orch = ConversationOrchestrator(brand_id=self.brand_id)
            
            # Test query
            query = "What's your return policy?"
            response, metadata = orch.process_message(query)
            
            # Check response length (should be substantial)
            self.assert_test(
                len(response) > 50,
                f"Response has substance: {len(response)} chars"
            )
            
            # Check brand name mentioned
            brand_name = self.brand_config.get('name', '')
            # Don't require brand name in response
            
            # Check emoji usage matches config
            voice_config = self.brand_config.get('voice', {})
            emoji_usage = voice_config.get('emoji_usage', 'none')
            has_emoji = any(ord(c) > 127 for c in response)
            
            if emoji_usage == 'none':
                self.assert_test(
                    not has_emoji,
                    f"No emojis (as configured)"
                )
            elif emoji_usage in ['moderate', 'frequent']:
                # Emoji usage is OK but not required
                self.assert_test(True, f"Emoji policy: {emoji_usage}")
            
            return True
        
        except Exception as e:
            self.assert_test(False, f"Response quality test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 70)
        print(f"🧪 BRAND TEST SUITE: {self.brand_id}")
        print("=" * 70)
        
        tests = [
            ("Brand Registration", self.test_brand_registration),
            ("Brand Voice", self.test_brand_voice),
            ("Session Creation", self.test_session_creation),
            ("Policy Retrieval", self.test_policy_retrieval),
            ("Data Isolation", self.test_data_isolation),
            ("Orchestrator", self.test_orchestrator),
            ("Integration Config", self.test_integration_config),
            ("Response Quality", self.test_response_quality),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.print_test(test_name)
                self.assert_test(False, f"Test crashed: {e}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\nTests Passed: {self.passed}/{total} ({success_rate:.1f}%)")
        print(f"Tests Failed: {self.failed}/{total}")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print(f"✅ Brand '{self.brand_id}' is ready for production!")
        elif self.failed <= 2:
            print(f"\n⚠️  Some tests failed, but brand is usable")
            print("   Review failed tests and fix if critical")
        else:
            print(f"\n❌ Multiple tests failed")
            print("   Brand needs fixes before production use")
        
        print("=" * 70)
        
        return self.failed == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_brand.py <brand_id>")
        sys.exit(1)
    
    brand_id = sys.argv[1]
    
    try:
        tester = BrandTester(brand_id)
        success = tester.run_all_tests()
        
        sys.exit(0 if success else 1)
    
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
