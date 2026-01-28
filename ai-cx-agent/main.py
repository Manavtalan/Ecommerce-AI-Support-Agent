#!/usr/bin/env python3
"""
AI Customer Experience Agent - Main Chat Interface
Interactive conversation with emotion-aware, context-retaining agent
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our components
from core.utils.brand_loader import BrandLoader
from core.orchestrator import ConversationOrchestrator


def print_header():
    """Print welcome header"""
    print()
    print("=" * 70)
    print("  🤖 AI CUSTOMER EXPERIENCE AGENT - FashionHub")
    print("=" * 70)
    print()
    print("  Welcome! I'm your FashionHub customer support assistant.")
    print("  I can help you with orders, returns, policies, and more!")
    print()
    print("  Type 'quit' or 'exit' to end the conversation")
    print("  Type 'help' for example queries")
    print("  Type 'stats' to see conversation statistics")
    print()
    print("=" * 70)
    print()


def print_help():
    """Print help information"""
    print()
    print("📋 EXAMPLE QUERIES:")
    print()
    print("  Order Status:")
    print("    • Where is order 12345?")
    print("    • When will my order arrive?")
    print("    • Can I track my order?")
    print()
    print("  Order Issues:")
    print("    • My order 12348 is LATE! (Try order 12348)")
    print("    • I received a damaged product (Try order 12353)")
    print("    • Wrong item received (Try order 12350)")
    print()
    print("  Policies:")
    print("    • What's your return policy?")
    print("    • How do I cancel my order?")
    print("    • Do you offer free shipping?")
    print()
    print("  Available Test Orders:")
    print("    • 12345 - Shipped order (normal)")
    print("    • 12348 - Delayed order (test frustration)")
    print("    • 12350 - Wrong size issue")
    print("    • 12353 - Damaged product")
    print()


def print_stats(orchestrator: ConversationOrchestrator):
    """Print conversation statistics"""
    summary = orchestrator.get_conversation_summary()
    
    print()
    print("📊 CONVERSATION STATISTICS:")
    print()
    print(f"  Total Messages: {summary['messages']}")
    print(f"  Messages Processed: {summary['total_processed']}")
    print()
    print("  Emotions Detected:")
    for emotion, count in summary['emotions_detected'].items():
        if count > 0:
            print(f"    • {emotion.title()}: {count}")
    print()
    
    # Context usage
    context_usage = orchestrator.get_context().get_context_window_usage()
    print(f"  Context Window Usage: {context_usage['percentage_used']:.1f}%")
    print(f"  Tokens Used: ~{context_usage['current_tokens']}")
    print()


def extract_order_id(message: str) -> str or None:
    """
    Extract order ID from message
    
    Simple pattern matching for order IDs like "12345"
    """
    import re
    # Look for 5-digit numbers
    match = re.search(r'\b\d{5}\b', message)
    return match.group(0) if match else None


def main():
    """Main chat loop"""
    
    # Print header
    print_header()
    
    # Initialize components
    print("🔄 Initializing AI agent...")
    print()
    
    try:
        # Load FashionHub brand
        brand = BrandLoader("fashionhub")
        print(f"✅ Loaded: {brand}")
        
        # Create orchestrator
        orchestrator = ConversationOrchestrator(
            brand_voice=brand.get_brand_voice(),
            system_prompt=brand.get_system_prompt()
        )
        print(f"✅ Created: {orchestrator}")
        
        print()
        print("✅ Agent ready! Start chatting...")
        print()
        print("-" * 70)
        
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        print()
        print("Please make sure:")
        print("  1. OPENAI_API_KEY is set in .env")
        print("  2. test_data/ directory exists with brand files")
        print()
        sys.exit(1)
    
    # Main conversation loop
    turn_number = 0
    current_order_id = None  # Track current order being discussed
    
    while True:
        try:
            # Get user input
            print()
            user_input = input("👤 You: ").strip()
            
            # Handle empty input
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print()
                print("👋 Thanks for chatting! Have a great day!")
                print()
                break
            
            if user_input.lower() == 'help':
                print_help()
                continue
            
            if user_input.lower() == 'stats':
                print_stats(orchestrator)
                continue
            
            if user_input.lower() == 'clear':
                orchestrator.clear_conversation()
                current_order_id = None
                print()
                print("🔄 Conversation cleared. Starting fresh!")
                print()
                turn_number = 0
                continue
            
            # Process message
            turn_number += 1
            
            # Try to extract order ID from message
            mentioned_order_id = extract_order_id(user_input)
            
            # If new order mentioned, update current order
            if mentioned_order_id:
                current_order_id = mentioned_order_id
            
            # Get order facts (use current_order_id if no new order mentioned)
            facts = {}
            order_id_to_use = current_order_id
            
            if order_id_to_use:
                order_facts = brand.get_order_facts(order_id_to_use)
                if "error" not in order_facts:
                    facts = order_facts
                    # Update context metadata
                    orchestrator.get_context().update_metadata("order_id", order_id_to_use)
            
            # Generate response through orchestrator
            print()
            print("🤖 Agent: ", end="", flush=True)
            
            response, metadata = orchestrator.process_message(
                user_message=user_input,
                facts=facts
            )
            
            # Print response
            print(response)
            
            # Show metadata in debug mode (optional)
            if os.getenv("DEBUG") == "true":
                print()
                print(f"   [Debug: emotion={metadata['emotion']}, "
                      f"intensity={metadata['intensity']}, "
                      f"scenario={metadata['scenario']}, "
                      f"order_id={current_order_id}]")
            
            print()
            print("-" * 70)
            
        except KeyboardInterrupt:
            print()
            print()
            print("👋 Interrupted. Goodbye!")
            print()
            break
        
        except Exception as e:
            print()
            print(f"❌ Error: {e}")
            print()
            
            if os.getenv("DEBUG") == "true":
                import traceback
                traceback.print_exc()
            
            print("Let's try again...")
            continue


if __name__ == "__main__":
    main()
