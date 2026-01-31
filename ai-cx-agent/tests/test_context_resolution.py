#!/usr/bin/env python3
"""
Test Context Resolution
Validates intelligent context handling
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import ConversationOrchestrator


def test_context_resolution():
    """Test context resolution with real orchestrator"""
    print("🧪 TESTING CONTEXT RESOLUTION")
    print("=" * 70)
    print()
    
    # Create orchestrator
    orch = ConversationOrchestrator(brand_id="fashionhub")
    
    print("TEST SCENARIO: Multi-turn order conversation")
    print("-" * 70)
    
    # Turn 1: Ask about order
    print("\n👤 User: Where's my order 12345?")
    response1, meta1 = orch.process_message("Where's my order 12345?")
    print(f"🤖 Agent: {response1[:150]}...")
    print(f"   Active topic: {meta1.get('active_topic')}")
    
    # Turn 2: Follow-up (should use context!)
    print("\n👤 User: Why is it late?")
    response2, meta2 = orch.process_message("Why is it late?")
    print(f"🤖 Agent: {response2[:150]}...")
    print(f"   Context maintained: {meta2.get('context_maintained')}")
    print(f"   Active topic: {meta2.get('active_topic')}")
    
    # Turn 3: Another follow-up
    print("\n👤 User: When will it arrive?")
    response3, meta3 = orch.process_message("When will it arrive?")
    print(f"🤖 Agent: {response3[:150]}...")
    print(f"   Context maintained: {meta3.get('context_maintained')}")
    
    # Turn 4: Topic switch
    print("\n👤 User: What's your return policy?")
    response4, meta4 = orch.process_message("What's your return policy?")
    print(f"🤖 Agent: {response4[:150]}...")
    print(f"   Context maintained: {meta4.get('context_maintained')}")
    print(f"   New topic: {meta4.get('active_topic')}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 CONTEXT RESOLUTION SUMMARY")
    print("=" * 70)
    
    summary = orch.get_conversation_summary()
    context_stats = summary['context_stats']
    
    print(f"\nContext Resolutions: {context_stats['context_resolutions']}")
    print(f"Context Maintained: {context_stats['context_maintained']}")
    print(f"Topic Switches: {context_stats['topic_switches']}")
    
    # Validation
    print("\n✅ VALIDATION:")
    
    # Should have resolved context at least once
    if context_stats['context_maintained'] >= 1:
        print("  ✅ Context was maintained across turns")
    else:
        print("  ⚠️  Context not maintained (check API key)")
    
    # Should have detected topic switch
    if context_stats['topic_switches'] >= 1:
        print("  ✅ Topic switches detected")
    else:
        print("  ⚠️  Topic switch not detected")
    
    print("\n🎉 Context resolution test complete!")


if __name__ == "__main__":
    test_context_resolution()
