#!/usr/bin/env python3
"""
Test Escalation Logic
Validates smart escalation triggers and prevention
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import ConversationOrchestrator


def test_escalation_scenarios():
    """Test various escalation scenarios"""
    print("🧪 TESTING ESCALATION LOGIC")
    print("=" * 70)
    print()
    
    # Create orchestrator
    orch = ConversationOrchestrator(brand_id="fashionhub")
    
    # Test scenarios
    test_cases = [
        {
            'name': 'Tier 1: Refund Request',
            'message': 'I want a refund immediately',
            'expected_escalation': True,
            'expected_tier': 1
        },
        {
            'name': 'Tier 1: Legal Threat',
            'message': 'I will take legal action against you',
            'expected_escalation': True,
            'expected_tier': 1
        },
        {
            'name': 'Tier 1: Cancellation (Post-Shipping)',
            'message': 'Cancel my order right now',
            'expected_escalation': True,
            'expected_tier': 1
        },
        {
            'name': 'Tier 2: Human Request',
            'message': 'I want to speak to a human',
            'expected_escalation': True,
            'expected_tier': 2
        },
        {
            'name': 'Tier 2: Manager Request',
            'message': 'Let me talk to your manager',
            'expected_escalation': True,
            'expected_tier': 2
        },
        {
            'name': 'Normal Query (No Escalation)',
            'message': 'Where is my order 12345?',
            'expected_escalation': False,
            'expected_tier': 0
        },
        {
            'name': 'Polite Question (No Escalation)',
            'message': 'Can you help me with my order?',
            'expected_escalation': False,
            'expected_tier': 0
        },
    ]
    
    print("ESCALATION TRIGGER TESTS")
    print("-" * 70)
    print()
    
    results = []
    
    for test in test_cases:
        print(f"TEST: {test['name']}")
        print(f"Message: '{test['message']}'")
        
        # Clear conversation for each test
        orch.clear_conversation()
        
        # Process message
        response, metadata = orch.process_message(test['message'])
        
        # Check escalation
        escalation = metadata.get('escalation')
        escalated = escalation is not None and escalation.get('should_escalate', False)
        tier = escalation.get('escalation_tier', 0) if escalation else 0
        
        # Validate
        escalation_match = escalated == test['expected_escalation']
        tier_match = tier == test['expected_tier']
        
        success = escalation_match and (tier_match if escalated else True)
        
        results.append(success)
        
        if success:
            print(f"✅ PASS")
        else:
            print(f"❌ FAIL")
            print(f"   Expected escalation: {test['expected_escalation']}, Got: {escalated}")
            if escalated:
                print(f"   Expected tier: {test['expected_tier']}, Got: {tier}")
        
        if escalation:
            print(f"   Tier: {tier}")
            print(f"   Reason: {escalation.get('reason')}")
            print(f"   Urgency: {escalation.get('urgency')}")
            print(f"   Message: {escalation.get('suggested_message', '')[:80]}...")
        else:
            print(f"   No escalation")
        
        print()
    
    # Summary
    print("=" * 70)
    print("📊 ESCALATION TEST SUMMARY")
    print("=" * 70)
    print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    # Stats
    summary = orch.get_conversation_summary()
    esc_stats = summary['escalation_stats']
    
    print()
    print("Escalation Statistics:")
    print(f"  Total triggered: {esc_stats['escalations_triggered']}")
    print(f"  Tier 1 (Critical): {esc_stats['tier1_escalations']}")
    print(f"  Tier 2 (Conditional): {esc_stats['tier2_escalations']}")
    print(f"  Prevented: {esc_stats['escalations_prevented']}")
    
    if passed == total:
        print()
        print("🎉 ALL ESCALATION TESTS PASSED!")
    
    return passed == total


def test_repeated_frustration():
    """Test escalation from repeated frustration"""
    print("\n" + "=" * 70)
    print("🧪 TESTING REPEATED FRUSTRATION ESCALATION")
    print("=" * 70)
    print()
    
    orch = ConversationOrchestrator(brand_id="fashionhub")
    
    messages = [
        "Where's my order?",
        "This is taking too long!",
        "This is ridiculous!",
        "I'm extremely frustrated!"
    ]
    
    print("Sending 4 increasingly frustrated messages...")
    print()
    
    for i, msg in enumerate(messages, 1):
        print(f"Message {i}: '{msg}'")
        response, metadata = orch.process_message(msg)
        
        escalation = metadata.get('escalation')
        if escalation:
            print(f"  🚨 ESCALATED!")
            print(f"     Tier: {escalation['escalation_tier']}")
            print(f"     Reason: {escalation['reason']}")
        else:
            print(f"  ✓ No escalation (emotion: {metadata['emotion']})")
        print()
    
    # Check if escalation happened by message 3 or 4
    summary = orch.get_conversation_summary()
    escalations = summary['escalation_stats']['escalations_triggered']
    
    if escalations >= 1:
        print("✅ Repeated frustration triggered escalation")
        return True
    else:
        print("⚠️  Repeated frustration did not trigger escalation")
        return False


def test_escalation_prevention():
    """Test that empathy prevents premature escalation"""
    print("\n" + "=" * 70)
    print("🧪 TESTING ESCALATION PREVENTION")
    print("=" * 70)
    print()
    
    orch = ConversationOrchestrator(brand_id="fashionhub")
    
    # First frustrated message - should try empathy first
    print("Sending first frustrated message...")
    msg = "I'm really frustrated with this delay"
    
    response, metadata = orch.process_message(msg)
    
    escalation = metadata.get('escalation')
    
    if escalation and escalation.get('prevent_escalation'):
        print("✅ Escalation prevented - trying empathy first")
        print(f"   Suggested: {escalation.get('suggested_message', '')[:80]}...")
        return True
    elif not escalation:
        print("✓ No escalation on first frustration (as expected)")
        return True
    else:
        print("⚠️  Escalated immediately (should try empathy first)")
        return False


if __name__ == "__main__":
    print()
    
    # Run all tests
    test1 = test_escalation_scenarios()
    test2 = test_repeated_frustration()
    test3 = test_escalation_prevention()
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 FINAL ESCALATION TEST RESULTS")
    print("=" * 70)
    print()
    
    tests_passed = sum([test1, test2, test3])
    total_tests = 3
    
    print(f"Test Suites Passed: {tests_passed}/{total_tests}")
    print()
    
    if test1:
        print("✅ Trigger tests: PASS")
    else:
        print("❌ Trigger tests: FAIL")
    
    if test2:
        print("✅ Repeated frustration: PASS")
    else:
        print("❌ Repeated frustration: FAIL")
    
    if test3:
        print("✅ Escalation prevention: PASS")
    else:
        print("❌ Escalation prevention: FAIL")
    
    print()
    
    if tests_passed == total_tests:
        print("🎉🎉🎉 ALL ESCALATION TESTS PASSED! 🎉🎉🎉")
        print()
        print("✅ Tier 1 (Critical) escalations working")
        print("✅ Tier 2 (Conditional) escalations working")
        print("✅ Repeated frustration detection working")
        print("✅ Escalation prevention working")
        print()
        print("🚀 Escalation system ready for production!")
    else:
        print(f"⚠️  {total_tests - tests_passed} test suite(s) failed")
    
    print()
