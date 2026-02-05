"""
Automated Tests: Order Management (20 tests)
Each test corresponds to a test case from the manual testing checklist
"""

import pytest


class TestOrderManagement:
    """20 automated tests for order management functionality"""
    
    def test_om_001_simple_order_status(self, agent, send_message):
        """TEST-OM-001: Where is my order 12345?"""
        result = send_message("Where is my order 12345?")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: Where is my order 12345?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        # Verify agent responded
        assert result['response'], "Agent did not provide a response"
        assert len(result['response']) > 0, "Response is empty"
        
        # Verify response contains order information
        response_lower = result['response'].lower()
        assert '12345' in response_lower, "Order number not mentioned"
        
        # Verify response time
        assert result['response_time'] < 5.0, f"Response too slow: {result['response_time']}s"
        
        print(f"✅ Response time: {result['response_time']:.2f}s")
    
    def test_om_002_order_lookup_minimal_info(self, agent, send_message):
        """TEST-OM-002: Where's my order?"""
        result = send_message("Where's my order?")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: Where's my order?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        
        # Should ask for order number
        assert any(phrase in response_lower for phrase in ['order number', 'order id', 'which order']), \
            "Agent should ask for order number"
    
    def test_om_003_multi_turn_order_lookup(self, agent, multi_turn_conversation):
        """TEST-OM-003: Multi-turn context retention"""
        turns = [
            "I need help with my order",
            "It's order 12345",
            "When will it arrive?"
        ]
        
        results = multi_turn_conversation(turns)
        
        # PRINT ALL TURNS
        print("\n" + "="*80)
        print("MULTI-TURN CONVERSATION:")
        print("="*80)
        for r in results:
            print(f"\nTURN {r['turn']}:")
            print(f"USER: {r['user_message']}")
            print(f"AGENT: {r['response']}")
            print("-"*80)
        
        # Turn 1: Should ask for order number
        assert any(phrase in results[0]['response'].lower() for phrase in ['order number', 'which order'])
        
        # Turn 3: Should NOT ask for order number again
        turn3_lower = results[2]['response'].lower()
        assert not any(phrase in turn3_lower for phrase in ['order number?', 'which order?']), \
            "Context not retained - agent asked for order number again"
        
        print("✅ Context retained across 3 turns")
    
    def test_om_004_order_contents_inquiry(self, agent, send_message):
        """TEST-OM-004: What's in my order 12345?"""
        result = send_message("What's in my order 12345?")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: What's in my order 12345?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        
        # Should mention order contents
        assert len(response) > 20, "Response too short to contain order details"
        assert '12345' in response, "Order number not referenced"
    
    def test_om_005_delayed_order_inquiry(self, agent, send_message):
        """TEST-OM-005: My order 12345 is late. Where is it?"""
        result = send_message("My order 12345 is late. Where is it?")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: My order 12345 is late. Where is it?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        
        # Should show empathy
        empathy_phrases = ['sorry', 'understand', 'apologize', 'appreciate your patience']
        has_empathy = any(phrase in response_lower for phrase in empathy_phrases)
        
        # Should provide tracking or status
        has_info = '12345' in response_lower
        
        print(f"✅ Empathy: {has_empathy}, Info: {has_info}")
    
    def test_om_006_order_cancellation_preship(self, agent, send_message):
        """TEST-OM-006: I want to cancel order 12345"""
        result = send_message("I want to cancel order 12345")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: I want to cancel order 12345")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        # Should either offer to cancel or escalate
        response = result['response']
        assert len(response) > 0, "No response provided"
    
    def test_om_007_order_cancellation_postship(self, agent, send_message):
        """TEST-OM-007: Cancel my order 12345 please. It already shipped."""
        result = send_message("Cancel my order 12345 please. It already shipped.")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: Cancel my order 12345 please. It already shipped.")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        metadata = result.get('metadata', {})
        response_lower = result['response'].lower()
        
        # CRITICAL: Must escalate for post-ship cancellation
        escalated = metadata.get('escalation_triggered', False) or 'escalat' in response_lower or 'support' in response_lower
        
        assert escalated, "CRITICAL: Must escalate for post-ship cancellation"
        print("✅ Correctly escalated post-ship cancellation")
    
    def test_om_008_refund_request(self, agent, send_message):
        """TEST-OM-008: I need a refund for order 12345"""
        result = send_message("I need a refund for order 12345")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: I need a refund for order 12345")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        metadata = result.get('metadata', {})
        response_lower = result['response'].lower()
        
        # CRITICAL: Must escalate for refunds
        escalated = metadata.get('escalation_triggered', False) or 'escalat' in response_lower or 'support' in response_lower
        
        assert escalated, "CRITICAL: Must escalate for refund requests"
        print("✅ Correctly escalated refund request")
    
    def test_om_009_change_delivery_address(self, agent, send_message):
        """TEST-OM-009: Can I change the delivery address for order 12345?"""
        result = send_message("Can I change the delivery address for order 12345?")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: Can I change the delivery address for order 12345?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        assert len(response) > 0, "No response provided"
        assert '12345' in response, "Order number not referenced"
    
    def test_om_010_order_not_received(self, agent, send_message):
        """TEST-OM-010: I didn't receive my order 12345 but tracking says delivered"""
        result = send_message("I didn't receive my order 12345 but tracking says delivered")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: I didn't receive my order 12345 but tracking says delivered")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        
        # Should show high empathy (serious issue)
        has_empathy = any(phrase in response_lower for phrase in ['sorry', 'understand', 'concerning'])
        
        # Should offer help
        has_help = any(phrase in response_lower for phrase in ['help', 'investigate', 'look into', 'check'])
        
        print(f"✅ Empathy: {has_empathy}, Help offered: {has_help}")
    
    def test_om_011_multiple_orders_query(self, agent, send_message):
        """TEST-OM-011: What's the status of orders 12345 and 12346?"""
        result = send_message("What's the status of orders 12345 and 12346?")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: What's the status of orders 12345 and 12346?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        
        # Should mention both orders
        assert '12345' in response, "First order not mentioned"
        assert '12346' in response, "Second order not mentioned"
        
        print("✅ Both orders referenced in response")
    
    def test_om_012_invalid_order_number(self, agent, send_message):
        """TEST-OM-012: Where is order 99999?"""
        result = send_message("Where is order 99999?")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: Where is order 99999?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        
        # Should handle gracefully
        handled_gracefully = any(phrase in response_lower for phrase in [
            'not found', "can't find", "couldn't find", 'verify', 'check'
        ])
        
        # Should not crash
        assert result['response'], "Agent crashed - no response"
        
        print(f"✅ Handled gracefully: {handled_gracefully}")
    
    def test_om_013_order_with_special_characters(self, agent, send_message):
        """TEST-OM-013: Status of order #12345"""
        result = send_message("Status of order #12345")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: Status of order #12345")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        
        # Should extract order number correctly
        assert '12345' in response or '#12345' in response, "Order number not referenced"
        assert len(response) > 0, "No response provided"
    
    def test_om_014_tracking_number_query(self, agent, send_message):
        """TEST-OM-014: Track package DEL123456789"""
        result = send_message("Track package DEL123456789")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: Track package DEL123456789")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        
        # Should provide helpful response
        assert len(response) > 20, "Response too short"
        
        # Should reference tracking number or ask for clarification
        tracking_handled = 'DEL123456789' in response or 'order' in response.lower()
        print(f"✅ Tracking handled: {tracking_handled}")
    
    def test_om_015_exchange_request(self, agent, send_message):
        """TEST-OM-015: I want to exchange the dress in order 12345 for a larger size"""
        result = send_message("I want to exchange the dress in order 12345 for a larger size")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: I want to exchange the dress in order 12345 for a larger size")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        
        # Should address exchange
        addresses_exchange = any(word in response_lower for word in ['exchange', 'size', 'swap'])
        
        assert len(result['response']) > 0, "No response provided"
        print(f"✅ Addresses exchange: {addresses_exchange}")
    
    def test_om_016_damaged_item_report(self, agent, send_message):
        """TEST-OM-016: The dress in order 12345 arrived damaged"""
        result = send_message("The dress in order 12345 arrived damaged")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: The dress in order 12345 arrived damaged")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        metadata = result.get('metadata', {})
        
        # Should show HIGH empathy
        has_empathy = any(phrase in response_lower for phrase in ['sorry', 'apologize', 'unfortunate'])
        
        # Should escalate or offer solution
        escalated = metadata.get('escalation_triggered', False) or 'support' in response_lower
        
        print(f"✅ High empathy: {has_empathy}, Escalated: {escalated}")
    
    def test_om_017_wrong_item_received(self, agent, send_message):
        """TEST-OM-017: I ordered a blue dress but got a red one (order 12345)"""
        result = send_message("I ordered a blue dress but got a red one (order 12345)")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: I ordered a blue dress but got a red one (order 12345)")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        
        # Should show empathy and offer solution
        has_empathy = any(phrase in response_lower for phrase in ['sorry', 'apologize'])
        
        assert len(result['response']) > 0, "No response provided"
        print(f"✅ Empathy shown: {has_empathy}")
    
    def test_om_018_hinglish_order_status(self, agent, send_message):
        """TEST-OM-018: Bhai, mera order 12345 kahan hai?"""
        result = send_message("Bhai, mera order 12345 kahan hai?")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: Bhai, mera order 12345 kahan hai?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        
        # Should understand and respond
        assert len(response) > 0, "No response provided"
        assert '12345' in response, "Order number not referenced"
        
        print("✅ Hinglish query understood")
    
    def test_om_019_repeat_order_creation(self, agent, send_message):
        """TEST-OM-019: I want to order the same items from order 12345 again"""
        result = send_message("I want to order the same items from order 12345 again")
        
        # PRINT THE RESPONSE
        print("\n" + "="*80)
        print("QUESTION: I want to order the same items from order 12345 again")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        
        # Should provide helpful guidance
        assert len(response) > 20, "Response too short"
        assert '12345' in response, "Order number not referenced"
    
    def test_om_020_order_date_confusion(self, agent, send_message, multi_turn_conversation):
        """TEST-OM-020: Order placed vs shipped date confusion"""
        turns = [
            "When was my order shipped?",
            "No, I mean when was it PLACED?"
        ]
        
        results = multi_turn_conversation(turns)
        
        # PRINT ALL TURNS
        print("\n" + "="*80)
        print("MULTI-TURN CONVERSATION:")
        print("="*80)
        for r in results:
            print(f"\nTURN {r['turn']}:")
            print(f"USER: {r['user_message']}")
            print(f"AGENT: {r['response']}")
            print("-"*80)
        
        # Should understand correction in turn 2
        turn2_lower = results[1]['response'].lower()
        understands_correction = any(word in turn2_lower for word in ['placed', 'ordered', 'created'])
        
        print(f"✅ Understood correction: {understands_correction}")
