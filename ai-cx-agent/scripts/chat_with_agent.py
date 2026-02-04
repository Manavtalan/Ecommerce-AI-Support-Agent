#!/usr/bin/env python3
"""
Interactive Chat with AI CX Agent
Test your agent in real-time!
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import ConversationOrchestrator
import time


def print_banner():
    """Print welcome banner"""
    print("\n" + "="*70)
    print("🤖 AI CX AGENT - INTERACTIVE CHAT")
    print("="*70)
    print()
    print("Test your AI agent with real conversations!")
    print("Type 'exit' or 'quit' to end the session")
    print("Type 'switch <brand>' to change brands")
    print("Type 'stats' to see conversation statistics")
    print()


def print_stats(orch):
    """Print conversation statistics"""
    print("\n" + "="*70)
    print("📊 CONVERSATION STATISTICS")
    print("="*70)
    print()
    print(f"Brand: {orch.brand_config.get('name')}")
    print(f"Messages: {orch.total_messages_processed}")
    print(f"Tool Calls: {orch.tool_stats.get('tool_calls', 0)}")
    print(f"Escalations: {orch.escalation_stats.get('escalations_triggered', 0)}")
    print()
    
    if orch.quality_stats:
        print("Quality Scores:")
        print(f"  Overall: {orch.quality_stats.get('avg_overall', 0):.1f}/10")
        print(f"  Empathy: {orch.quality_stats.get('avg_empathy', 0):.1f}/10")
        print(f"  Accuracy: {orch.quality_stats.get('avg_accuracy', 0):.1f}/10")
    print()


def chat_session(brand_id="fashionhub"):
    """Run interactive chat session"""
    
    print_banner()
    
    print(f"🎯 Starting session with: {brand_id}")
    print("⏳ Loading agent...")
    
    orch = ConversationOrchestrator(brand_id=brand_id)
    
    print(f"✅ Agent loaded for: {orch.brand_config.get('name')}")
    print()
    print("-" * 70)
    print()
    
    turn = 0
    
    while True:
        # Get user input
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        # Handle commands
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\n👋 Thanks for testing! Goodbye!")
            break
        
        if user_input.lower() == 'stats':
            print_stats(orch)
            continue
        
        if user_input.lower().startswith('switch '):
            new_brand = user_input.split(' ', 1)[1].strip()
            print(f"\n🔄 Switching to brand: {new_brand}")
            try:
                orch = ConversationOrchestrator(brand_id=new_brand)
                print(f"✅ Switched to: {orch.brand_config.get('name')}\n")
                turn = 0
            except Exception as e:
                print(f"❌ Error switching brand: {e}\n")
            continue
        
        # Process message
        turn += 1
        print()
        
        start_time = time.time()
        
        try:
            response, metadata = orch.process_message(user_input)
            duration = (time.time() - start_time) * 1000
            
            # Print agent response
            print(f"Agent: {response}")
            print()
            
            # Print metadata
            print(f"💡 Quality: {metadata['quality_score']['overall']:.1f}/10 ({metadata['quality_score']['grade']})")
            print(f"⚡ Response time: {duration:.0f}ms")
            
            if metadata.get('tool_used'):
                print(f"🔧 Tool used: {metadata['tool_used']}")
            
            if metadata.get('emotion') != 'neutral':
                print(f"😊 Emotion: {metadata['emotion']} ({metadata.get('intensity', 0):.1f})")
            
            if metadata.get('escalation'):
                print(f"🚨 Escalation: Tier {metadata['escalation']['escalation_tier']}")
            
            print()
            print("-" * 70)
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    
    # Check for brand argument
    brand_id = "fashionhub"
    
    if len(sys.argv) > 1:
        brand_id = sys.argv[1]
    
    # Start chat session
    chat_session(brand_id)


if __name__ == "__main__":
    main()
