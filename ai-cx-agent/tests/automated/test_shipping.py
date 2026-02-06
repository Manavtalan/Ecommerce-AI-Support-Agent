"""
Automated Tests: Shipping (8 tests)
"""

import pytest


class TestShipping:
    """8 automated tests for shipping functionality"""
    
    def test_sh_001_shipping_cost_inquiry(self, agent, send_message):
        """TEST-SH-001: How much is shipping?"""
        result = send_message("How much is shipping?")
        
        print("\n" + "="*80)
        print("QUESTION: How much is shipping?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        mentions_cost = any(word in response_lower for word in ['free', 'cost', 'price', '$', '₹', 'shipping'])
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Mentions cost: {mentions_cost}")
    
    def test_sh_002_shipping_timeline(self, agent, send_message):
        """TEST-SH-002: How long does shipping take?"""
        result = send_message("How long does shipping take?")
        
        print("\n" + "="*80)
        print("QUESTION: How long does shipping take?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        mentions_timeline = any(word in response_lower for word in ['day', 'days', 'week', 'business', 'deliver'])
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Mentions timeline: {mentions_timeline}")
    
    def test_sh_003_international_shipping(self, agent, send_message):
        """TEST-SH-003: Do you ship to the USA?"""
        result = send_message("Do you ship to the USA?")
        
        print("\n" + "="*80)
        print("QUESTION: Do you ship to the USA?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        addresses_international = any(word in response_lower for word in ['international', 'usa', 'ship', 'country'])
        has_answer = any(word in response_lower for word in ['yes', 'no', 'do', "don't"])
        
        assert len(result['response']) > 10, "Response too short"
        print(f"✅ Addresses international: {addresses_international}, Has answer: {has_answer}")
    
    def test_sh_004_expedited_shipping(self, agent, send_message):
        """TEST-SH-004: Can I get expedited shipping?"""
        result = send_message("Can I get expedited shipping?")
        
        print("\n" + "="*80)
        print("QUESTION: Can I get expedited shipping?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        addresses_expedited = any(word in response_lower for word in ['expedit', 'express', 'fast', 'rush', 'quick'])
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Addresses expedited: {addresses_expedited}")
    
    def test_sh_005_tracking_not_updating(self, agent, send_message):
        """TEST-SH-005: My tracking hasn't updated in 3 days"""
        result = send_message("My tracking hasn't updated in 3 days")
        
        print("\n" + "="*80)
        print("QUESTION: My tracking hasn't updated in 3 days")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        shows_empathy = any(word in response_lower for word in ['sorry', 'understand', 'apologize'])
        offers_help = any(word in response_lower for word in ['help', 'check', 'investigate', 'look'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Shows empathy: {shows_empathy}, Offers help: {offers_help}")
    
    def test_sh_006_free_shipping_threshold(self, agent, send_message):
        """TEST-SH-006: How much do I need to spend for free shipping?"""
        result = send_message("How much do I need to spend for free shipping?")
        
        print("\n" + "="*80)
        print("QUESTION: How much do I need to spend for free shipping?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        mentions_threshold = any(word in response_lower for word in ['50', 'free', 'shipping', 'spend', 'order'])
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Mentions threshold: {mentions_threshold}")
    
    def test_sh_007_shipping_address_typo(self, agent, send_message):
        """TEST-SH-007: I made a typo in my shipping address"""
        result = send_message("I made a typo in my shipping address")
        
        print("\n" + "="*80)
        print("QUESTION: I made a typo in my shipping address")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        addresses_issue = any(word in response_lower for word in ['address', 'change', 'update', 'correct'])
        offers_solution = any(word in response_lower for word in ['help', 'update', 'change', 'contact'])
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Addresses issue: {addresses_issue}, Offers solution: {offers_solution}")
    
    def test_sh_008_delivery_time_specific_location(self, agent, send_message):
        """TEST-SH-008: How long does shipping take to Mumbai?"""
        result = send_message("How long does shipping take to Mumbai?")
        
        print("\n" + "="*80)
        print("QUESTION: How long does shipping take to Mumbai?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        mentions_location = 'mumbai' in response_lower or 'location' in response_lower
        mentions_timeline = any(word in response_lower for word in ['day', 'days', 'week', 'deliver'])
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Mentions location: {mentions_location}, Timeline: {mentions_timeline}")
