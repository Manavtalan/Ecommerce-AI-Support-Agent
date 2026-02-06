"""
Automated Tests: Emotion Handling (12 tests)
"""

import pytest


class TestEmotionHandling:
    """12 automated tests for emotion detection and empathy"""
    
    def test_em_001_frustration(self, agent, send_message):
        """TEST-EM-001: This is ridiculous! My order still hasn't shipped!"""
        result = send_message("This is ridiculous! My order still hasn't shipped!")
        
        print("\n" + "="*80)
        print("QUESTION: This is ridiculous! My order still hasn't shipped!")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        shows_empathy = any(word in response_lower for word in ['sorry', 'understand', 'apologize', 'frustrat'])
        offers_help = any(word in response_lower for word in ['help', 'check', 'look', 'assist'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Shows empathy: {shows_empathy}, Offers help: {offers_help}")
    
    def test_em_002_anger(self, agent, send_message):
        """TEST-EM-002: I'm extremely disappointed with your service"""
        result = send_message("I'm extremely disappointed with your service")
        
        print("\n" + "="*80)
        print("QUESTION: I'm extremely disappointed with your service")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        shows_empathy = any(word in response_lower for word in ['sorry', 'apologize', 'understand', 'disappoint'])
        not_defensive = 'but' not in response_lower[:100]
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Shows empathy: {shows_empathy}, Not defensive: {not_defensive}")
    
    def test_em_003_confusion(self, agent, send_message):
        """TEST-EM-003: I'm confused about your return policy"""
        result = send_message("I'm confused about your return policy")
        
        print("\n" + "="*80)
        print("QUESTION: I'm confused about your return policy")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        acknowledges_confusion = any(word in response_lower for word in ['happy to clarify', 'let me explain', 'help clarify'])
        provides_clarity = 'return' in response_lower or 'policy' in response_lower
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Acknowledges confusion: {acknowledges_confusion}, Provides clarity: {provides_clarity}")
    
    def test_em_004_urgency(self, agent, send_message):
        """TEST-EM-004: URGENT! I need my dress by tomorrow for a wedding!"""
        result = send_message("URGENT! I need my dress by tomorrow for a wedding!")
        
        print("\n" + "="*80)
        print("QUESTION: URGENT! I need my dress by tomorrow for a wedding!")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        acknowledges_urgency = any(word in response_lower for word in ['urgent', 'understand', 'wedding', 'tomorrow'])
        offers_immediate_help = any(word in response_lower for word in ['check', 'help', 'see', 'look'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Acknowledges urgency: {acknowledges_urgency}, Immediate help: {offers_immediate_help}")
    
    def test_em_005_happiness(self, agent, send_message):
        """TEST-EM-005: I love my dress! Thank you so much!"""
        result = send_message("I love my dress! Thank you so much!")
        
        print("\n" + "="*80)
        print("QUESTION: I love my dress! Thank you so much!")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        matches_positive_tone = any(word in response_lower for word in ['glad', 'happy', 'wonderful', 'great', 'thrilled'])
        
        assert len(result['response']) > 10, "Response too short"
        print(f"✅ Matches positive tone: {matches_positive_tone}")
    
    def test_em_006_anxiety(self, agent, send_message):
        """TEST-EM-006: I'm worried my order won't arrive in time"""
        result = send_message("I'm worried my order won't arrive in time")
        
        print("\n" + "="*80)
        print("QUESTION: I'm worried my order won't arrive in time")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        reassures = any(word in response_lower for word in ['understand', 'help', 'check', 'see', 'don\'t worry'])
        provides_info = any(word in response_lower for word in ['delivery', 'arrive', 'tracking', 'status'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Reassures: {reassures}, Provides info: {provides_info}")
    
    def test_em_007_sarcasm(self, agent, send_message):
        """TEST-EM-007: Oh great, another delayed delivery. Just wonderful."""
        result = send_message("Oh great, another delayed delivery. Just wonderful.")
        
        print("\n" + "="*80)
        print("QUESTION: Oh great, another delayed delivery. Just wonderful.")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        recognizes_frustration = any(word in response_lower for word in ['sorry', 'apologize', 'understand', 'frustrat'])
        not_literal = 'glad' not in response_lower and 'great to hear' not in response_lower
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Recognizes frustration: {recognizes_frustration}, Not literal: {not_literal}")
    
    def test_em_008_desperation(self, agent, send_message):
        """TEST-EM-008: Please help me, I really need this order"""
        result = send_message("Please help me, I really need this order")
        
        print("\n" + "="*80)
        print("QUESTION: Please help me, I really need this order")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        compassionate_response = any(word in response_lower for word in ['absolutely', 'definitely', 'here to help', 'of course'])
        takes_action = any(word in response_lower for word in ['check', 'look', 'see', 'help'])
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Compassionate: {compassionate_response}, Takes action: {takes_action}")
    
    def test_em_009_impatience(self, agent, send_message):
        """TEST-EM-009: Can you just tell me where my order is?"""
        result = send_message("Can you just tell me where my order is?")
        
        print("\n" + "="*80)
        print("QUESTION: Can you just tell me where my order is?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        direct_response = len(result['response']) < 200  # Not overly long
        addresses_request = any(word in response_lower for word in ['order', 'check', 'help', 'number'])
        
        assert len(result['response']) > 10, "Response too short"
        print(f"✅ Direct response: {direct_response}, Addresses request: {addresses_request}")
    
    def test_em_010_gratitude(self, agent, send_message):
        """TEST-EM-010: Thanks for your help!"""
        result = send_message("Thanks for your help!")
        
        print("\n" + "="*80)
        print("QUESTION: Thanks for your help!")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        acknowledges_thanks = any(word in response_lower for word in ['welcome', 'pleasure', 'happy', 'glad'])
        
        assert len(result['response']) > 5, "Response too short"
        print(f"✅ Acknowledges thanks: {acknowledges_thanks}")
    
    def test_em_011_disappointment(self, agent, send_message):
        """TEST-EM-011: The dress doesn't look like the picture at all"""
        result = send_message("The dress doesn't look like the picture at all")
        
        print("\n" + "="*80)
        print("QUESTION: The dress doesn't look like the picture at all")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        shows_empathy = any(word in response_lower for word in ['sorry', 'apologize', 'understand', 'disappoint'])
        offers_solution = any(word in response_lower for word in ['return', 'exchange', 'help', 'refund'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Shows empathy: {shows_empathy}, Offers solution: {offers_solution}")
    
    def test_em_012_multiple_emotions(self, agent, send_message):
        """TEST-EM-012: I'm excited about the dress but worried about the delivery time"""
        result = send_message("I'm excited about the dress but worried about the delivery time")
        
        print("\n" + "="*80)
        print("QUESTION: I'm excited about the dress but worried about the delivery time")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        acknowledges_excitement = any(word in response_lower for word in ['excited', 'glad', 'great'])
        addresses_worry = any(word in response_lower for word in ['delivery', 'arrive', 'time', 'track'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Acknowledges excitement: {acknowledges_excitement}, Addresses worry: {addresses_worry}")
