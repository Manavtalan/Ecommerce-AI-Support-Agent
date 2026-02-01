#!/usr/bin/env python3
"""Debug LLM calls to see what's happening"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import ConversationOrchestrator

print("🔍 DEBUGGING LLM CALLS")
print("=" * 70)
print()

orch = ConversationOrchestrator(brand_id="fashionhub")

# Get composer stats before
print("Composer Stats BEFORE:")
print(orch.composer.get_retry_stats())
print()

# Send a message
print("Sending: 'Where is my order 12345?'")
response, metadata = orch.process_message("Where is my order 12345?")

print()
print("Response received:")
print(response)
print()

# Get composer stats after
print("Composer Stats AFTER:")
stats = orch.composer.get_retry_stats()
print(stats)
print()

if stats['failed_calls'] > 0:
    print("❌ LLM CALLS ARE FAILING!")
    print("   All responses are using fallbacks")
    print("   This explains the generic responses")
elif stats['successful_calls'] > 0:
    print("✅ LLM calls working")
    print("   Should be getting real responses")
else:
    print("⚠️  No LLM calls made at all!")
