#!/usr/bin/env python3
"""
End-to-End Test Suite
Tests complete system with all 10 original test conversations
Validates: Context retention, quality scores, tool usage
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import ConversationOrchestrator
import time


class TestConversation:
    """Test conversation runner"""
    
    def __init__(self, name, messages, expected):
        self.name = name
        self.messages = messages
        self.expected = expected
        self.results = []
        self.passed = False
    
    def run(self, brand_id="fashionhub"):
        """Run test conversation"""
        print(f"\n{'='*70}")
        print(f"TEST: {self.name}")
        print(f"{'='*70}")
        
        orch = ConversationOrchestrator(brand_id=brand_id)
        
        all_responses = []
        quality_scores = []
        tools_used = set()
        
        for i, message in enumerate(self.messages, 1):
            print(f"\n[Turn {i}] User: {message}")
            
            start_time = time.time()
            response, metadata = orch.process_message(message)
            duration = (time.time() - start_time) * 1000
            
            print(f"[Turn {i}] Agent: {response[:100]}{'...' if len(response) > 100 else ''}")
            print(f"[Turn {i}] Quality: {metadata['quality_score']['overall']:.1f}/10")
            print(f"[Turn {i}] Duration: {duration:.0f}ms")
            
            all_responses.append(response)
            quality_scores.append(metadata['quality_score']['overall'])
            
            if metadata.get('tool_used'):
                tools_used.add(metadata['tool_used'])
        
        # Validate expectations
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        checks = {
            'min_quality': avg_quality >= self.expected.get('quality_min', 7.0),
            'context_maintained': orch.context_stats.get('context_maintained', 0) > 0 if self.expected.get('context_maintained') else True,
            'tools_used': all(tool in tools_used for tool in self.expected.get('tools_used', [])) if self.expected.get('tools_used') else True
        }
        
        self.passed = all(checks.values())
        
        # Summary
        print(f"\n{'='*70}")
        print(f"RESULTS: {self.name}")
        print(f"{'='*70}")
        print(f"Average Quality: {avg_quality:.1f}/10")
        print(f"Context Maintained: {orch.context_stats.get('context_maintained', 0)} times")
        print(f"Tools Used: {', '.join(tools_used) if tools_used else 'None'}")
        print(f"Status: {'✅ PASS' if self.passed else '❌ FAIL'}")
        
        return self.passed


def run_all_tests():
    """Run all 10 test conversations"""
    
    print("🧪 END-TO-END TEST SUITE")
    print("=" * 70)
    print()
    
    # Define all 10 test conversations
    tests = [
        TestConversation(
            name="1. Order Tracking",
            messages=[
                "Where is my order 12345?",
                "When will it arrive?",
                "Can I track it?"
            ],
            expected={
                'context_maintained': True,
                'tools_used': ['get_order_status'],
                'quality_min': 7.0
            }
        ),
        TestConversation(
            name="2. Return Policy",
            messages=[
                "What's your return policy?",
                "Can I return after 30 days?",
                "How do I initiate a return?"
            ],
            expected={
                'tools_used': ['search_knowledge'],
                'quality_min': 7.0
            }
        ),
        TestConversation(
            name="3. Product Information",
            messages=[
                "Tell me about the Blue Denim Jacket",
                "What sizes do you have?",
                "Is it available in medium?"
            ],
            expected={
                'tools_used': ['get_product_info'],
                'quality_min': 7.0
            }
        ),
        TestConversation(
            name="4. Shipping Eligibility",
            messages=[
                "Do you ship to California?",
                "How much is shipping?",
                "How long does it take?"
            ],
            expected={
                'tools_used': ['check_shipping_eligibility'],
                'quality_min': 7.0
            }
        ),
        TestConversation(
            name="5. Multiple Questions",
            messages=[
                "I need help with my order 12345 and want to know your return policy",
                "Also, do you have the jacket in stock?",
                "Thanks for all the help!"
            ],
            expected={
                'quality_min': 7.0
            }
        ),
        TestConversation(
            name="6. Frustrated Customer",
            messages=[
                "This is ridiculous! My order is late!",
                "I've been waiting for weeks!",
                "What are you going to do about it?"
            ],
            expected={
                'quality_min': 6.5  # Lower due to emotion handling
            }
        ),
        TestConversation(
            name="7. General Inquiry",
            messages=[
                "What are your business hours?",
                "Can I visit your store?",
                "Do you have a phone number?"
            ],
            expected={
                'tools_used': ['search_knowledge'],
                'quality_min': 7.0
            }
        ),
        TestConversation(
            name="8. Context Switching",
            messages=[
                "Where is order 12345?",
                "Actually, tell me about your exchange policy",
                "Never mind, back to my order - when will it ship?"
            ],
            expected={
                'context_maintained': True,
                'quality_min': 7.0
            }
        ),
        TestConversation(
            name="9. Hinglish Query",
            messages=[
                "Bhai, mera order kahan hai?",
                "When will it arrive yaar?",
                "Thanks boss!"
            ],
            expected={
                'quality_min': 6.5
            }
        ),
        TestConversation(
            name="10. Long Conversation",
            messages=[
                "Hi there!",
                "I want to buy a jacket",
                "What colors do you have?",
                "Do you have it in blue?",
                "What's the price?",
                "Can you ship to New York?",
                "How long will shipping take?",
                "Great! What's your return policy?",
                "Can I return if it doesn't fit?",
                "Perfect, I'll order it!"
            ],
            expected={
                'context_maintained': True,
                'quality_min': 7.0
            }
        )
    ]
    
    # Run all tests
    results = []
    
    for test in tests:
        try:
            passed = test.run()
            results.append((test.name, passed))
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            results.append((test.name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Final summary
    print(f"\n{'='*70}")
    print("END-TO-END TEST SUMMARY")
    print(f"{'='*70}")
    print()
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Tests Passed: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    print()
    
    if passed_count == total_count:
        print("🎉 ALL END-TO-END TESTS PASSED!")
        print("✅ System ready for production")
        return True
    else:
        print(f"⚠️  {total_count - passed_count} test(s) failed")
        print("Review failures before deploying")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
