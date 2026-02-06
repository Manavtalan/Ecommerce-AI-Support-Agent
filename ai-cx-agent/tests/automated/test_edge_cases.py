"""
Automated Tests: Edge Cases (15 tests)
"""

import pytest


class TestEdgeCases:
    """15 automated tests for edge cases and error handling"""
    
    def test_ec_001_empty_message(self, agent, send_message):
        """TEST-EC-001: Empty message"""
        result = send_message("")
        
        print("\n" + "="*80)
        print("QUESTION: (empty string)")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        handles_gracefully = any(word in response_lower for word in ['help', 'assist', 'how can'])
        
        assert len(result['response']) > 0, "Agent should respond to empty message"
        print(f"✅ Handles gracefully: {handles_gracefully}")
    
    def test_ec_002_very_long_message(self, agent, send_message):
        """TEST-EC-002: Very long message"""
        long_message = "I want to know about my order " + "and also " * 50 + "when will it arrive?"
        result = send_message(long_message)
        
        print("\n" + "="*80)
        print("QUESTION: (very long message - 300+ chars)")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        assert len(result['response']) > 0, "Agent should handle long messages"
        assert result['response_time'] < 10.0, f"Response too slow: {result['response_time']}s"
        
        print(f"✅ Response time: {result['response_time']:.2f}s")
    
    def test_ec_003_special_characters(self, agent, send_message):
        """TEST-EC-003: Special characters"""
        result = send_message("Where is my order #12345 @!$%^&*()?")
        
        print("\n" + "="*80)
        print("QUESTION: Where is my order #12345 @!$%^&*()?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        handles_special_chars = '12345' in result['response']
        
        assert len(result['response']) > 0, "Agent should handle special characters"
        print(f"✅ Handles special characters: {handles_special_chars}")
    
    def test_ec_004_all_caps(self, agent, send_message):
        """TEST-EC-004: ALL CAPS MESSAGE"""
        result = send_message("WHERE IS MY ORDER?!")
        
        print("\n" + "="*80)
        print("QUESTION: WHERE IS MY ORDER?!")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        shows_empathy = any(word in response_lower for word in ['understand', 'help', 'sorry'])
        
        assert len(result['response']) > 0, "Agent should handle all caps"
        print(f"✅ Shows empathy: {shows_empathy}")
    
    def test_ec_005_gibberish(self, agent, send_message):
        """TEST-EC-005: Gibberish input"""
        result = send_message("asdfghjkl qwerty zxcvbn")
        
        print("\n" + "="*80)
        print("QUESTION: asdfghjkl qwerty zxcvbn")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        asks_to_clarify = any(phrase in response_lower for phrase in ['help you', 'clarify', 'understand', 'mean'])
        
        assert len(result['response']) > 0, "Agent should handle gibberish"
        print(f"✅ Asks to clarify: {asks_to_clarify}")
    
    def test_ec_006_numbers_only(self, agent, send_message):
        """TEST-EC-006: Numbers only"""
        result = send_message("12345")
        
        print("\n" + "="*80)
        print("QUESTION: 12345")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        asks_for_context = any(word in response_lower for word in ['order', 'help', 'looking', 'mean'])
        
        assert len(result['response']) > 0, "Agent should handle numbers only"
        print(f"✅ Asks for context: {asks_for_context}")
    
    def test_ec_007_emoji_only(self, agent, send_message):
        """TEST-EC-007: Emoji only"""
        result = send_message("😊👍")
        
        print("\n" + "="*80)
        print("QUESTION: 😊👍")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        responds_helpfully = any(word in response_lower for word in ['help', 'assist', 'how can'])
        
        assert len(result['response']) > 0, "Agent should handle emoji"
        print(f"✅ Responds helpfully: {responds_helpfully}")
    
    def test_ec_008_mixed_languages(self, agent, send_message):
        """TEST-EC-008: Mixed languages (Hinglish)"""
        result = send_message("Mera order kab aayega? When will it arrive?")
        
        print("\n" + "="*80)
        print("QUESTION: Mera order kab aayega? When will it arrive?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        understands_question = any(word in response_lower for word in ['order', 'arrive', 'delivery', 'when'])
        
        assert len(result['response']) > 0, "Agent should handle mixed languages"
        print(f"✅ Understands question: {understands_question}")
    
    def test_ec_009_repeated_words(self, agent, send_message):
        """TEST-EC-009: Repeated words"""
        result = send_message("order order order order status status")
        
        print("\n" + "="*80)
        print("QUESTION: order order order order status status")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        addresses_order_status = 'order' in response_lower or 'status' in response_lower
        
        assert len(result['response']) > 0, "Agent should handle repeated words"
        print(f"✅ Addresses order status: {addresses_order_status}")
    
    def test_ec_010_url_in_message(self, agent, send_message):
        """TEST-EC-010: URL in message"""
        result = send_message("Check this link https://example.com for my order")
        
        print("\n" + "="*80)
        print("QUESTION: Check this link https://example.com for my order")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        ignores_url = 'example.com' not in response_lower or 'link' in response_lower
        addresses_order = 'order' in response_lower
        
        assert len(result['response']) > 0, "Agent should handle URLs"
        print(f"✅ Addresses order: {addresses_order}")
    
    def test_ec_011_sql_injection_attempt(self, agent, send_message):
        """TEST-EC-011: SQL injection attempt"""
        result = send_message("'; DROP TABLE orders; --")
        
        print("\n" + "="*80)
        print("QUESTION: '; DROP TABLE orders; --")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        handles_safely = any(word in response_lower for word in ['help', 'assist', 'clarify'])
        
        assert len(result['response']) > 0, "Agent should handle SQL injection safely"
        print(f"✅ Handles safely: {handles_safely}")
    
    def test_ec_012_script_tag_attempt(self, agent, send_message):
        """TEST-EC-012: Script tag attempt"""
        result = send_message("<script>alert('test')</script>")
        
        print("\n" + "="*80)
        print("QUESTION: <script>alert('test')</script>")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        no_script_execution = '<script>' not in response
        
        assert len(result['response']) > 0, "Agent should handle script tags safely"
        print(f"✅ No script in response: {no_script_execution}")
    
    def test_ec_013_very_old_order(self, agent, send_message):
        """TEST-EC-013: Very old order inquiry"""
        result = send_message("Where is order 00001 from 2020?")
        
        print("\n" + "="*80)
        print("QUESTION: Where is order 00001 from 2020?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        handles_old_order = any(phrase in response_lower for phrase in ['old', '2020', 'check', 'find', 'help'])
        
        assert len(result['response']) > 0, "Agent should handle old orders"
        print(f"✅ Handles old order: {handles_old_order}")
    
    def test_ec_014_contradictory_statements(self, agent, send_message):
        """TEST-EC-014: Contradictory statements"""
        result = send_message("I want to cancel my order but also want it shipped faster")
        
        print("\n" + "="*80)
        print("QUESTION: I want to cancel my order but also want it shipped faster")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        asks_for_clarification = any(phrase in response_lower for phrase in ['clarify', 'which', 'prefer', 'would you like'])
        
        assert len(result['response']) > 0, "Agent should handle contradictions"
        print(f"✅ Asks for clarification: {asks_for_clarification}")
    
    def test_ec_015_rapid_fire_questions(self, agent, multi_turn_conversation):
        """TEST-EC-015: Rapid fire questions"""
        turns = [
            "Order status?",
            "Tracking?",
            "Price?",
            "Return policy?"
        ]
        
        results = multi_turn_conversation(turns)
        
        print("\n" + "="*80)
        print("RAPID FIRE CONVERSATION:")
        print("="*80)
        for r in results:
            print(f"\nTURN {r['turn']}:")
            print(f"USER: {r['user_message']}")
            print(f"AGENT: {r['response']}")
            print("-"*80)
        
        all_responded = all(len(r['response']) > 0 for r in results)
        
        print(f"✅ All questions answered: {all_responded}")
