#!/usr/bin/env python3
"""
Integration Readiness Tests
Tests all integration adapters with mock data
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.integrations.whatsapp_adapter import WhatsAppMessageAdapter
from core.integrations.whatsapp_formatter import WhatsAppResponseFormatter
from core.integrations.email_adapter import EmailAdapter
from core.integrations.instagram_adapter import InstagramDMAdapter
from core.orchestrator import ConversationOrchestrator


def test_whatsapp_integration():
    """Test WhatsApp message flow"""
    print("\n" + "="*70)
    print("TEST: WhatsApp Integration")
    print("="*70)
    
    adapter = WhatsAppMessageAdapter()
    formatter = WhatsAppResponseFormatter()
    
    # Mock WhatsApp message
    mock_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.test123",
                        "timestamp": "1234567890",
                        "type": "text",
                        "text": {"body": "Where is my order 12345?"}
                    }]
                }
            }]
        }]
    }
    
    # Parse message
    parsed = adapter.parse_incoming_message(mock_payload)
    print(f"✅ Message parsed: {parsed['user_message']}")
    
    # Process with agent
    orch = ConversationOrchestrator(brand_id="fashionhub")
    response, metadata = orch.process_message(parsed['user_message'])
    print(f"✅ Agent processed: {response[:60]}...")
    
    # Format response
    formatted = formatter.format_response(response, {
        'scenario': metadata.get('scenario'),
        'order_data': metadata.get('order_data')
    })
    print(f"✅ Response formatted: {formatted['type']}")
    print(f"✅ Buttons: {len(formatted.get('buttons', []))}")
    
    return True


def test_email_integration():
    """Test Email flow"""
    print("\n" + "="*70)
    print("TEST: Email Integration")
    print("="*70)
    
    adapter = EmailAdapter(brand_config={
        'name': 'FashionHub',
        'support_email': 'support@fashionhub.com'
    })
    
    # Mock email
    mock_email = {
        'subject': 'Question about order',
        'body': 'Hi, where is my order 12345?',
        'from': 'customer@example.com'
    }
    
    # Parse email
    parsed = adapter.parse_email(mock_email)
    print(f"✅ Email parsed: {parsed['user_message']}")
    
    # Process with agent
    orch = ConversationOrchestrator(brand_id="fashionhub")
    response, metadata = orch.process_message(parsed['user_message'])
    print(f"✅ Agent processed: {response[:60]}...")
    
    # Format response
    formatted = adapter.format_email_response(response, {
        'subject': mock_email['subject'],
        'thread_id': parsed['session_id'],
        'user_email': parsed['user_email']
    })
    print(f"✅ Email formatted: {formatted['subject']}")
    print(f"✅ HTML generated: {len(formatted['body_html'])} chars")
    
    return True


def test_instagram_integration():
    """Test Instagram DM flow"""
    print("\n" + "="*70)
    print("TEST: Instagram DM Integration")
    print("="*70)
    
    adapter = InstagramDMAdapter()
    
    # Mock Instagram DM
    mock_dm = {
        "object": "instagram",
        "entry": [{
            "messaging": [{
                "sender": {"id": "ig_user_123"},
                "recipient": {"id": "ig_page_456"},
                "timestamp": 1234567890,
                "message": {
                    "mid": "mid.test",
                    "text": "Do you have blue jackets?"
                }
            }]
        }]
    }
    
    # Parse DM
    parsed = adapter.parse_dm(mock_dm)
    print(f"✅ DM parsed: {parsed['user_message']}")
    
    # Process with agent
    orch = ConversationOrchestrator(brand_id="fashionhub")
    response, metadata = orch.process_message(parsed['user_message'])
    print(f"✅ Agent processed: {response[:60]}...")
    
    # Format response
    formatted = adapter.format_dm_response(response, {
        'scenario': metadata.get('scenario')
    })
    print(f"✅ DM formatted: {formatted['message_count']} message(s)")
    print(f"✅ Quick replies: {len(formatted.get('quick_replies', []))}")
    
    return True


def test_integration_readiness():
    """Run all integration tests"""
    
    print("🧪 INTEGRATION READINESS TESTS")
    print("=" * 70)
    print()
    
    tests = [
        ("WhatsApp", test_whatsapp_integration),
        ("Email", test_email_integration),
        ("Instagram", test_instagram_integration)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    print()
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name} Integration")
    
    print()
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"Integrations Passed: {passed_count}/{total_count}")
    print()
    
    if passed_count == total_count:
        print("🎉 ALL INTEGRATIONS READY!")
        return True
    else:
        print(f"⚠️  {total_count - passed_count} integration(s) failed")
        return False


if __name__ == "__main__":
    success = test_integration_readiness()
    sys.exit(0 if success else 1)
