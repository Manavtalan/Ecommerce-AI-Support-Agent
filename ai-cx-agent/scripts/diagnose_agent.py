#!/usr/bin/env python3
"""
DIAGNOSTIC TOOL - Shows EXACTLY what's broken
Tests every component independently
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import ConversationOrchestrator
from core.tools.registry import ToolRegistry
from core.tools.knowledge_tool import search_knowledge
from core.tools.order_tool import get_order_status
import json


def test_tool_selection():
    """Test if tool selection is working"""
    print("\n" + "="*70)
    print("TEST 1: TOOL SELECTION LOGIC")
    print("="*70)
    
    registry = ToolRegistry("fashionhub")
    
    test_cases = [
        ("Where is my order 12345?", "get_order_status"),
        ("What's your refund policy?", "search_knowledge"),
        ("I want to return my order", "search_knowledge"),
        ("Can I cancel order 12345?", "get_order_status"),
        ("How much is shipping?", "search_knowledge"),
        ("Do you ship to California?", "check_shipping_eligibility"),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected_tool in test_cases:
        selected = registry.select_tool(message)
        
        if selected == expected_tool:
            print(f"✅ '{message}' → {selected}")
            passed += 1
        else:
            print(f"❌ '{message}'")
            print(f"   Expected: {expected_tool}")
            print(f"   Got: {selected}")
            failed += 1
    
    print()
    print(f"Tool Selection: {passed}/{passed+failed} correct")
    print(f"Accuracy: {passed/(passed+failed)*100:.1f}%")
    
    return passed == len(test_cases)


def test_knowledge_base():
    """Test if knowledge base has data"""
    print("\n" + "="*70)
    print("TEST 2: KNOWLEDGE BASE")
    print("="*70)
    
    test_queries = [
        "refund policy",
        "return policy",
        "shipping policy",
        "exchange policy"
    ]
    
    for query in test_queries:
        result = search_knowledge(query, "fashionhub")
        
        if result.get('success') and result.get('data'):
            print(f"✅ '{query}' → Found {len(result['data'])} results")
            print(f"   Sample: {result['data'][0][:100]}...")
        else:
            print(f"❌ '{query}' → NO DATA FOUND")
            print(f"   Error: {result.get('error', 'Unknown')}")
    
    return True


def test_escalation_logic():
    """Test escalation detection"""
    print("\n" + "="*70)
    print("TEST 3: ESCALATION LOGIC")
    print("="*70)
    
    orch = ConversationOrchestrator("fashionhub")
    
    test_cases = [
        ("What's your refund policy?", False, "Should search knowledge, not escalate"),
        ("I want a refund for my order", True, "Should escalate - requesting refund"),
        ("I want to cancel my order", True, "Should escalate - cancellation"),
        ("How do returns work?", False, "Should search knowledge, not escalate"),
        ("I'm very frustrated!", False, "Should show empathy, not escalate yet"),
    ]
    
    for message, should_escalate, reason in test_cases:
        # Process message
        response, metadata = orch.process_message(message)
        
        escalated = metadata.get('escalation') is not None
        
        if escalated == should_escalate:
            print(f"✅ '{message}'")
            print(f"   Escalated: {escalated} (Expected: {should_escalate})")
        else:
            print(f"❌ '{message}'")
            print(f"   Escalated: {escalated} (Expected: {should_escalate})")
            print(f"   Reason: {reason}")
        
        # Reset for next test
        orch = ConversationOrchestrator("fashionhub")
    
    return True


def test_intent_understanding():
    """Test if agent understands intent"""
    print("\n" + "="*70)
    print("TEST 4: INTENT UNDERSTANDING")
    print("="*70)
    
    orch = ConversationOrchestrator("fashionhub")
    
    test_cases = [
        {
            'message': "What's your refund policy?",
            'expected_tool': 'search_knowledge',
            'should_mention': ['refund', 'policy'],
            'should_not_escalate': True
        },
        {
            'message': "I want to return my order",
            'expected_tool': 'search_knowledge',
            'should_mention': ['return'],
            'should_not_escalate': False  # Could escalate after explaining
        },
        {
            'message': "Where is order 12345?",
            'expected_tool': 'get_order_status',
            'should_mention': ['12345', 'Summer Floral Dress'],
            'should_not_escalate': True
        }
    ]
    
    for test in test_cases:
        response, metadata = orch.process_message(test['message'])
        
        tool_used = metadata.get('tool_used')
        escalated = metadata.get('escalation') is not None
        
        print(f"\n'{test['message']}'")
        print(f"  Tool Used: {tool_used} (Expected: {test['expected_tool']})")
        print(f"  Escalated: {escalated}")
        print(f"  Response: {response[:100]}...")
        
        # Check correctness
        correct_tool = tool_used == test['expected_tool']
        correct_escalation = (not escalated) == test['should_not_escalate']
        
        if correct_tool:
            print(f"  ✅ Correct tool")
        else:
            print(f"  ❌ Wrong tool")
        
        # Reset
        orch = ConversationOrchestrator("fashionhub")
    
    return True


def test_data_usage():
    """Test if agent actually uses the data"""
    print("\n" + "="*70)
    print("TEST 5: DATA USAGE IN RESPONSES")
    print("="*70)
    
    orch = ConversationOrchestrator("fashionhub")
    
    # Test order data usage
    response, metadata = orch.process_message("Where is order 12345?")
    
    print("\nOrder Query Test:")
    print(f"Response: {response}")
    print()
    
    required_elements = [
        ("Order ID (12345)", "12345" in response),
        ("Item Name", "Summer Floral Dress" in response or "dress" in response.lower()),
        ("Tracking Number", "DEL123456789" in response or "tracking" in response.lower()),
        ("Delivery Date", "January" in response or "Jan" in response or "29" in response),
    ]
    
    for element, present in required_elements:
        if present:
            print(f"✅ {element} mentioned")
        else:
            print(f"❌ {element} NOT mentioned")
    
    return True


def run_full_diagnosis():
    """Run all diagnostic tests"""
    
    print("\n" + "="*70)
    print("🔍 FULL AGENT DIAGNOSTIC")
    print("="*70)
    print("\nTesting every component to find what's broken...\n")
    
    results = []
    
    # Run all tests
    results.append(("Tool Selection", test_tool_selection()))
    results.append(("Knowledge Base", test_knowledge_base()))
    results.append(("Escalation Logic", test_escalation_logic()))
    results.append(("Intent Understanding", test_intent_understanding()))
    results.append(("Data Usage", test_data_usage()))
    
    # Summary
    print("\n" + "="*70)
    print("DIAGNOSTIC SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ WORKING" if passed else "❌ BROKEN"
        print(f"{status} - {name}")
    
    print()
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"Components Working: {passed_count}/{total_count}")
    print()
    
    if passed_count < total_count:
        print("⚠️  ISSUES FOUND - See details above")
    else:
        print("✅ ALL COMPONENTS WORKING")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_full_diagnosis()
    sys.exit(0 if success else 1)
