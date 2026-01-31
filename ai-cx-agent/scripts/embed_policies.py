#!/usr/bin/env python3
"""
Policy Embedding Script
Embeds brand policies into RAG system
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.brands.policy_uploader import PolicyUploader


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/embed_policies.py <brand_id>")
        sys.exit(1)
    
    brand_id = sys.argv[1]
    
    print(f"📚 Embedding policies for brand: {brand_id}")
    print("=" * 70)
    
    try:
        uploader = PolicyUploader(brand_id)
        
        # Check status
        status = uploader.get_upload_status()
        print(f"\nStatus:")
        print(f"  Policies found: {status['policies_uploaded']}")
        print(f"  Coverage:")
        for policy_type, exists in status['policy_coverage'].items():
            icon = "✅" if exists else "❌"
            print(f"    {icon} {policy_type}")
        
        if not status['ready_for_embedding']:
            print("\n⚠️  No policies to embed!")
            sys.exit(1)
        
        # Embed
        print("\n" + "=" * 70)
        result = uploader.embed_policies()
        
        if result.get('success'):
            print("\n✅ Policies embedded successfully!")
        else:
            print(f"\n❌ Embedding failed: {result.get('reason')}")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
