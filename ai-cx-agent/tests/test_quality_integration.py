#!/usr/bin/env python3
"""
Test Quality Scoring Integration
Validates quality monitoring in real conversations
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import ConversationOrchestrator


def test_quality_scoring():
    """Test quality scoring in real conversation"""
    print("🧪 TESTING QUALITY SCORING INTEGRATION")
    print("=" * 70)
    print()
    
    # Create orchestrator
    orch = ConversationOrchestrator(brand_id="fashionhub")
    
    # Conversation with varying quality
    messages = [
        ("Where's my order 12345?", "Should score well - has context"),
        ("Why is it late?", "Should use context - good quality"),
        ("This is ridiculous!", "Needs empathy - will score lower without it"),
        ("What's your return policy?", "New topic - should switch gracefully"),
    ]
    
    print("QUALITY TRACKING TEST")
    print("-" * 70)
    print()
    
    for i, (message, expectation) in enumerate(messages, 1):
        print(f"Turn {i}: '{message}'")
        print(f"Expected: {expectation}")
        
        response, metadata = orch.process_message(message)
        
        quality = metadata['quality_score']
        
        print(f"Response: {response[:100]}...")
        print()
        print(f"📊 Quality Scores:")
        print(f"   Overall: {quality['overall']}/10 ({quality['grade']})")
        print(f"   Context: {quality['context_retention']}/10")
        print(f"   Empathy: {quality['empathy']}/10")
        print(f"   Accuracy: {quality['accuracy']}/10")
        print(f"   Efficiency: {quality['efficiency']}/10")
        print(f"   Brand Voice: {quality['brand_voice']}/10")
        
        if quality['suggestions']:
            print(f"   💡 Suggestions:")
            for suggestion in quality['suggestions']:
                print(f"      - {suggestion}")
        
        print()
        print("-" * 70)
        print()
    
    # Summary
    summary = orch.get_conversation_summary()
    quality_stats = summary['quality_stats']
    
    print("=" * 70)
    print("📊 CONVERSATION QUALITY SUMMARY")
    print("=" * 70)
    print()
    print(f"Messages Processed: {summary['messages']}")
    print()
    print(f"Average Quality Scores:")
    print(f"  Overall: {quality_stats['avg_overall']}/10")
    print(f"  Context Retention: {quality_stats['avg_context']}/10")
    print(f"  Empathy: {quality_stats['avg_empathy']}/10")
    print(f"  Accuracy: {quality_stats['avg_accuracy']}/10")
    print(f"  Efficiency: {quality_stats['avg_efficiency']}/10")
    print(f"  Brand Voice: {quality_stats['avg_brand_voice']}/10")
    print()
    
    # Validation
    print("✅ VALIDATION:")
    
    if quality_stats['avg_overall'] >= 7.0:
        print(f"  ✅ Average quality is good ({quality_stats['avg_overall']}/10)")
    else:
        print(f"  ⚠️  Average quality needs improvement ({quality_stats['avg_overall']}/10)")
    
    if len(orch.quality_history) == 4:
        print(f"  ✅ All {len(orch.quality_history)} exchanges scored")
    
    # Check that quality varies (not all the same)
    scores = [q['overall'] for q in orch.quality_history]
    if len(set(scores)) > 1:
        print(f"  ✅ Quality scores vary appropriately (range: {min(scores):.1f}-{max(scores):.1f})")
    
    print()
    print("🎉 Quality scoring integration test complete!")


if __name__ == "__main__":
    test_quality_scoring()
