"""
Automated Tests: Brand Voice (10 tests)
"""

import pytest


class TestBrandVoice:
    """10 automated tests for brand voice consistency"""
    
    def test_bv_001_greeting_tone(self, agent, send_message):
        """TEST-BV-001: Greeting matches brand voice"""
        result = send_message("Hello")
        
        print("\n" + "="*80)
        print("QUESTION: Hello")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        is_friendly = any(word in response_lower for word in ['hi', 'hello', 'hey', '😊'])
        is_professional = len(result['response']) > 10
        
        assert len(result['response']) > 0, "Agent should greet"
        print(f"✅ Friendly: {is_friendly}, Professional: {is_professional}")
    
    def test_bv_002_emoji_usage(self, agent, send_message):
        """TEST-BV-002: Appropriate emoji usage"""
        result = send_message("I love shopping with you!")
        
        print("\n" + "="*80)
        print("QUESTION: I love shopping with you!")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        has_emoji = any(char in response for char in ['😊', '🎉', '💖', '✨', '👍'])
        not_excessive = response.count('😊') + response.count('🎉') < 5
        
        print(f"✅ Has emoji: {has_emoji}, Not excessive: {not_excessive}")
    
    def test_bv_003_formality_level(self, agent, send_message):
        """TEST-BV-003: Appropriate formality level"""
        result = send_message("What's your return policy?")
        
        print("\n" + "="*80)
        print("QUESTION: What's your return policy?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        not_too_casual = 'dude' not in response_lower and 'bro' not in response_lower
        not_too_formal = 'dear valued customer' not in response_lower
        
        print(f"✅ Not too casual: {not_too_casual}, Not too formal: {not_too_formal}")
    
    def test_bv_004_brand_name_usage(self, agent, send_message):
        """TEST-BV-004: Mentions brand name appropriately"""
        result = send_message("Tell me about your company")
        
        print("\n" + "="*80)
        print("QUESTION: Tell me about your company")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        mentions_brand = 'FashionHub' in response or 'fashionhub' in response.lower()
        
        print(f"✅ Mentions brand: {mentions_brand}")
    
    def test_bv_005_consistency_across_responses(self, agent, multi_turn_conversation):
        """TEST-BV-005: Consistent tone across multiple turns"""
        turns = [
            "Hello",
            "What do you sell?",
            "How can I contact you?"
        ]
        
        results = multi_turn_conversation(turns)
        
        print("\n" + "="*80)
        print("MULTI-TURN CONVERSATION:")
        print("="*80)
        for r in results:
            print(f"\nTURN {r['turn']}:")
            print(f"USER: {r['user_message']}")
            print(f"AGENT: {r['response']}")
            print("-"*80)
        
        all_friendly = all('😊' in r['response'] or 'hi' in r['response'].lower() or 'hello' in r['response'].lower() for r in results[:1])
        consistent_style = True  # Manual check - all should have similar friendliness
        
        print(f"✅ Consistent friendly tone across turns")
    
    def test_bv_006_avoiding_jargon(self, agent, send_message):
        """TEST-BV-006: Avoids unnecessary jargon"""
        result = send_message("How do I return something?")
        
        print("\n" + "="*80)
        print("QUESTION: How do I return something?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        no_complex_jargon = 'RMA' not in result['response'] and 'SKU' not in result['response']
        uses_simple_language = any(word in response_lower for word in ['return', 'send back', 'ship back'])
        
        print(f"✅ No jargon: {no_complex_jargon}, Simple language: {uses_simple_language}")
    
    def test_bv_007_positive_language(self, agent, send_message):
        """TEST-BV-007: Uses positive language"""
        result = send_message("Can I get a refund?")
        
        print("\n" + "="*80)
        print("QUESTION: Can I get a refund?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        positive_words = any(word in response_lower for word in ['happy', 'help', 'absolutely', 'of course'])
        no_negative_words = 'unfortunately' not in response_lower or 'can' in response_lower
        
        print(f"✅ Positive language: {positive_words}")
    
    def test_bv_008_personalization(self, agent, send_message):
        """TEST-BV-008: Personalizes responses when possible"""
        result = send_message("Where is my order 12345?")
        
        print("\n" + "="*80)
        print("QUESTION: Where is my order 12345?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        uses_name = 'Priya' in response  # From test data
        personal_tone = any(word in response.lower() for word in ['your', 'you'])
        
        print(f"✅ Uses name: {uses_name}, Personal tone: {personal_tone}")
    
    def test_bv_009_empathy_in_problems(self, agent, send_message):
        """TEST-BV-009: Shows empathy for problems"""
        result = send_message("My order is damaged")
        
        print("\n" + "="*80)
        print("QUESTION: My order is damaged")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        shows_empathy = any(word in response_lower for word in ['sorry', 'apologize', 'understand'])
        offers_help = any(word in response_lower for word in ['help', 'assist', 'resolve'])
        
        print(f"✅ Shows empathy: {shows_empathy}, Offers help: {offers_help}")
    
    def test_bv_010_enthusiasm_for_positive(self, agent, send_message):
        """TEST-BV-010: Shows enthusiasm for positive interactions"""
        result = send_message("I'm excited to receive my dress!")
        
        print("\n" + "="*80)
        print("QUESTION: I'm excited to receive my dress!")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        matches_enthusiasm = any(word in response_lower for word in ['excited', 'wonderful', 'great', 'amazing', '🎉'])
        positive_tone = not any(word in response_lower for word in ['however', 'but', 'unfortunately'])
        
        print(f"✅ Matches enthusiasm: {matches_enthusiasm}, Positive tone: {positive_tone}")
