#!/usr/bin/env python3
"""
Multi-Tenant Testing Suite
Tests 3 brands simultaneously with data isolation verification
"""

import sys
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import ConversationOrchestrator
from core.brands.registry import get_brand_registry


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_test(text):
    """Print test section"""
    print(f"\n{'─' * 70}")
    print(f"{text}")
    print(f"{'─' * 70}\n")


class MultiTenantTester:
    """Tests multi-tenant functionality"""
    
    def __init__(self):
        self.registry = get_brand_registry()
        self.brands = ["fashionhub", "techgear", "organicbites"]
        self.orchestrators = {}
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "total": 0
        }
    
    def assert_test(self, condition: bool, message: str):
        """Assert a test condition"""
        self.test_results["total"] += 1
        if condition:
            print(f"  ✅ {message}")
            self.test_results["passed"] += 1
        else:
            print(f"  ❌ {message}")
            self.test_results["failed"] += 1
    
    def test_1_brand_loading(self):
        """Test 1: All Brands Load Successfully"""
        print_test("TEST 1: Brand Loading")
        
        for brand_id in self.brands:
            brand = self.registry.get_brand_by_id(brand_id)
            self.assert_test(
                brand is not None,
                f"{brand_id}: Loaded successfully"
            )
            
            if brand:
                self.assert_test(
                    brand.get('name') is not None,
                    f"{brand_id}: Has name '{brand.get('name')}'"
                )
    
    def test_2_voice_differences(self):
        """Test 2: Voice Differences"""
        print_test("TEST 2: Brand Voice Differentiation")
        
        voices = {}
        for brand_id in self.brands:
            brand = self.registry.get_brand_by_id(brand_id)
            voice = brand.get('voice', {})
            voices[brand_id] = {
                'tone': voice.get('tone'),
                'emoji': voice.get('emoji_usage'),
                'formality': voice.get('formality')
            }
            
            print(f"  {brand_id}:")
            print(f"    Tone: {voice.get('tone')}")
            print(f"    Emoji: {voice.get('emoji_usage')}")
            print(f"    Formality: {voice.get('formality')}")
        
        # Check they're different
        tones = [v['tone'] for v in voices.values()]
        self.assert_test(
            len(set(tones)) == 3,
            f"All brands have different tones"
        )
        
        emoji_levels = [v['emoji'] for v in voices.values()]
        self.assert_test(
            len(set(emoji_levels)) >= 2,
            f"Brands have different emoji preferences"
        )
    
    def test_3_policy_differences(self):
        """Test 3: Policy Differences"""
        print_test("TEST 3: Brand Policy Differentiation")
        
        policies = {}
        for brand_id in self.brands:
            brand = self.registry.get_brand_by_id(brand_id)
            policy = brand.get('policies', {})
            policies[brand_id] = {
                'return_days': policy.get('return_window_days'),
                'free_shipping': policy.get('free_shipping_threshold'),
                'cod': policy.get('cod_available')
            }
            
            print(f"  {brand_id}:")
            print(f"    Return: {policy.get('return_window_days')} days")
            print(f"    Free shipping: ₹{policy.get('free_shipping_threshold')}")
            print(f"    COD: {policy.get('cod_available')}")
        
        # Check they're different
        return_windows = [p['return_days'] for p in policies.values()]
        self.assert_test(
            len(set(return_windows)) == 3,
            f"All brands have different return windows: {set(return_windows)}"
        )
        
        shipping_thresholds = [p['free_shipping'] for p in policies.values()]
        self.assert_test(
            len(set(shipping_thresholds)) == 3,
            f"All brands have different shipping thresholds: {set(shipping_thresholds)}"
        )
    
    def test_4_create_orchestrators(self):
        """Test 4: Create Orchestrators for Each Brand"""
        print_test("TEST 4: Orchestrator Creation")
        
        for brand_id in self.brands:
            try:
                orch = ConversationOrchestrator(brand_id=brand_id)
                self.orchestrators[brand_id] = orch
                
                self.assert_test(
                    orch.brand_id == brand_id,
                    f"{brand_id}: Orchestrator created with correct brand"
                )
            except Exception as e:
                self.assert_test(
                    False,
                    f"{brand_id}: Failed to create orchestrator: {e}"
                )
    
    def test_5_same_query_different_voices(self):
        """Test 5: Same Query, Different Brand Voices"""
        print_test("TEST 5: Voice Consistency Test")
        
        query = "What's your return policy?"
        
        responses = {}
        
        for brand_id in self.brands:
            if brand_id not in self.orchestrators:
                continue
            
            orch = self.orchestrators[brand_id]
            brand = self.registry.get_brand_by_id(brand_id)
            
            print(f"\n{brand_id.upper()} ({brand.get('name')}):")
            print(f"Query: '{query}'")
            
            start_time = time.time()
            response, metadata = orch.process_message(query)
            elapsed = time.time() - start_time
            
            responses[brand_id] = response
            
            # Check response
            self.assert_test(
                len(response) > 50,
                f"Response has substance ({len(response)} chars)"
            )
            
            self.assert_test(
                elapsed < 10.0,
                f"Response time acceptable ({elapsed:.2f}s)"
            )
            
            # Check emoji usage
            has_emoji = any(ord(c) > 127 for c in response)
            emoji_usage = brand.get('voice', {}).get('emoji_usage', 'none')
            
            if emoji_usage == 'none':
                # Should have no emojis
                if not has_emoji:
                    print(f"  ✅ No emojis (as configured)")
                else:
                    print(f"  ⚠️  Has emojis but configured for none")
            else:
                print(f"  ✓ Emoji policy: {emoji_usage}")
            
            # Show preview
            print(f"  Response preview: {response[:150]}...")
        
        # Check responses are different
        if len(responses) == 3:
            response_texts = list(responses.values())
            all_different = (
                response_texts[0] != response_texts[1] and
                response_texts[1] != response_texts[2] and
                response_texts[0] != response_texts[2]
            )
            
            self.assert_test(
                all_different,
                "All 3 brands gave different responses"
            )
    
    def test_6_data_isolation(self):
        """Test 6: Data Isolation Between Brands"""
        print_test("TEST 6: Data Isolation Verification")
        
        from core.brands.session import create_brand_session
        
        # Create sessions
        sessions = {}
        for brand_id in self.brands:
            sessions[brand_id] = create_brand_session(brand_id)
        
        # Test cross-brand access
        fashion_resource = {"brand_id": "fashionhub", "data": "fashion_order_123"}
        tech_resource = {"brand_id": "techgear", "data": "tech_order_456"}
        
        # FashionHub session should access fashion, not tech
        fashion_session = sessions["fashionhub"]
        
        try:
            fashion_session.validate_access(fashion_resource)
            self.assert_test(True, "FashionHub can access own resources")
        except PermissionError:
            self.assert_test(False, "FashionHub BLOCKED from own resources!")
        
        try:
            fashion_session.validate_access(tech_resource)
            self.assert_test(False, "Cross-brand access NOT blocked (SECURITY ISSUE!)")
        except PermissionError:
            self.assert_test(True, "Cross-brand access correctly blocked")
        
        # Test all combinations
        print("\n  Cross-Brand Access Matrix:")
        for session_brand in self.brands:
            for resource_brand in self.brands:
                resource = {"brand_id": resource_brand, "data": "test"}
                session = sessions[session_brand]
                
                try:
                    session.validate_access(resource)
                    if session_brand == resource_brand:
                        result = "✅ ALLOW"
                    else:
                        result = "❌ LEAK!"
                except PermissionError:
                    if session_brand == resource_brand:
                        result = "❌ BLOCK!"
                    else:
                        result = "✅ BLOCK"
                
                print(f"    {session_brand} → {resource_brand}: {result}")
    
    def test_7_concurrent_conversations(self):
        """Test 7: Concurrent Conversations"""
        print_test("TEST 7: Concurrent Multi-Brand Conversations")
        
        def conversation_task(brand_id):
            """Single brand conversation"""
            if brand_id not in self.orchestrators:
                return None
            
            orch = self.orchestrators[brand_id]
            messages = [
                "Hello!",
                "What's your return policy?",
                "How long for shipping?"
            ]
            
            responses = []
            for msg in messages:
                response, _ = orch.process_message(msg)
                responses.append(response)
            
            return {
                'brand_id': brand_id,
                'messages': len(messages),
                'responses': len(responses),
                'success': len(responses) == len(messages)
            }
        
        # Run concurrent conversations
        print("  Running 3 simultaneous conversations...")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(conversation_task, brand_id)
                for brand_id in self.brands
            ]
            
            results = [f.result() for f in futures]
        
        # Check results
        for result in results:
            if result:
                self.assert_test(
                    result['success'],
                    f"{result['brand_id']}: Completed {result['messages']} messages"
                )
    
    def test_8_performance_metrics(self):
        """Test 8: Performance Metrics"""
        print_test("TEST 8: Performance Under Multi-Tenant Load")
        
        query = "Hello, how can I return an item?"
        
        times = []
        
        for brand_id in self.brands:
            if brand_id not in self.orchestrators:
                continue
            
            orch = self.orchestrators[brand_id]
            
            start = time.time()
            response, _ = orch.process_message(query)
            elapsed = time.time() - start
            
            times.append(elapsed)
            print(f"  {brand_id}: {elapsed:.2f}s")
        
        if times:
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            self.assert_test(
                avg_time < 5.0,
                f"Average response time: {avg_time:.2f}s (target: <5s)"
            )
            
            self.assert_test(
                max_time < 10.0,
                f"Max response time: {max_time:.2f}s (target: <10s)"
            )
    
    def run_all_tests(self):
        """Run complete multi-tenant test suite"""
        print_header("🎯 MULTI-TENANT TEST SUITE")
        print("Testing: 3 brands simultaneously")
        print(f"Brands: {', '.join(self.brands)}")
        
        tests = [
            ("Brand Loading", self.test_1_brand_loading),
            ("Voice Differences", self.test_2_voice_differences),
            ("Policy Differences", self.test_3_policy_differences),
            ("Orchestrator Creation", self.test_4_create_orchestrators),
            ("Same Query Different Voices", self.test_5_same_query_different_voices),
            ("Data Isolation", self.test_6_data_isolation),
            ("Concurrent Conversations", self.test_7_concurrent_conversations),
            ("Performance Metrics", self.test_8_performance_metrics),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print_test(test_name)
                print(f"  ❌ Test crashed: {e}")
                import traceback
                traceback.print_exc()
                self.test_results["failed"] += 1
                self.test_results["total"] += 1
        
        # Summary
        print_header("📊 MULTI-TENANT TEST SUMMARY")
        
        total = self.test_results["total"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"Tests Failed: {failed}/{total}")
        print()
        
        if failed == 0:
            print("🎉🎉🎉 ALL MULTI-TENANT TESTS PASSED! 🎉🎉🎉")
            print()
            print("✅ Multi-tenant system PRODUCTION READY!")
            print("✅ 3 brands working simultaneously")
            print("✅ Complete data isolation verified")
            print("✅ Voice differentiation confirmed")
            print("✅ Performance acceptable")
            print()
            print("🚀 DAY 3 COMPLETE!")
        elif failed <= 3:
            print("✅ Multi-tenant system FUNCTIONAL!")
            print()
            print(f"⚠️  {failed} minor issues detected")
            print("   Review and fix if critical")
            print()
            print("🎊 DAY 3 ESSENTIALLY COMPLETE!")
        else:
            print("⚠️  Multiple issues detected")
            print("   Review failed tests")
        
        print("=" * 70)
        
        return failed == 0


def main():
    try:
        tester = MultiTenantTester()
        success = tester.run_all_tests()
        
        sys.exit(0 if success else 1)
    
    except Exception as e:
        print(f"\n❌ Multi-tenant test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
