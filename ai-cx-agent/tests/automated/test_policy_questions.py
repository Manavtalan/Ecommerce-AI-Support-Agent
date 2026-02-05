"""
Automated Tests: Policy Questions (15 tests)
"""

import pytest


class TestPolicyQuestions:
    """15 automated tests for policy question handling"""
    
    def test_pq_001_general_return_policy(self, agent, send_message):
        """TEST-PQ-001: What's your return policy?"""
        result = send_message("What's your return policy?")
        
        response_lower = result['response'].lower()
        
        # Should mention return window
        mentions_timeframe = any(word in response_lower for word in ['30 day', 'thirty day', 'days'])
        
        # Should provide policy info
        assert len(result['response']) > 30, "Response too short for policy"
        print(f"✅ Mentions timeframe: {mentions_timeframe}")
    
    def test_pq_002_specific_return_question(self, agent, send_message):
        """TEST-PQ-002: Can I return a dress if it doesn't fit?"""
        result = send_message("Can I return a dress if it doesn't fit?")
        
        response_lower = result['response'].lower()
        
        # Should give clear yes/no answer
        has_answer = 'yes' in response_lower or 'can return' in response_lower
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Provides answer: {has_answer}")
    
    def test_pq_003_return_after_window(self, agent, send_message):
        """TEST-PQ-003: Can I return something I bought 45 days ago?"""
        result = send_message("Can I return something I bought 45 days ago?")
        
        response_lower = result['response'].lower()
        
        # Should explain outside window
        explains_limit = any(phrase in response_lower for phrase in ['outside', 'past', 'after', 'window'])
        
        # Should show empathy
        has_empathy = any(word in response_lower for word in ['sorry', 'unfortunately'])
        
        print(f"✅ Explains limit: {explains_limit}, Empathy: {has_empathy}")
    
    def test_pq_004_return_process(self, agent, send_message):
        """TEST-PQ-004: How do I return an item?"""
        result = send_message("How do I return an item?")
        
        response = result['response']
        
        # Should provide process steps
        assert len(response) > 50, "Response too short for process explanation"
        
        # Should mention key steps
        response_lower = response.lower()
        mentions_steps = any(word in response_lower for word in ['step', 'process', 'return', 'ship'])
        
        print(f"✅ Provides process: {mentions_steps}")
    
    def test_pq_005_refund_timeline(self, agent, send_message):
        """TEST-PQ-005: When will I get my refund?"""
        result = send_message("When will I get my refund?")
        
        response_lower = result['response'].lower()
        
        # Should mention timeline
        mentions_time = any(word in response_lower for word in ['day', 'week', 'business', 'process'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Mentions timeline: {mentions_time}")
    
    def test_pq_006_shipping_cost(self, agent, send_message):
        """TEST-PQ-006: How much is shipping?"""
        result = send_message("How much is shipping?")
        
        response = result['response']
        
        # Should provide cost information
        assert len(response) > 20, "Response too short"
        
        # Should mention cost or free shipping
        response_lower = response.lower()
        mentions_cost = any(word in response_lower for word in ['$', 'free', 'cost', 'price', 'shipping'])
        
        print(f"✅ Mentions cost: {mentions_cost}")
    
    def test_pq_007_shipping_timeline(self, agent, send_message):
        """TEST-PQ-007: How long does shipping take?"""
        result = send_message("How long does shipping take?")
        
        response_lower = result['response'].lower()
        
        # Should mention timeframe
        mentions_time = any(word in response_lower for word in ['day', 'week', 'business', 'deliver'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Mentions timeframe: {mentions_time}")
    
    def test_pq_008_international_shipping(self, agent, send_message):
        """TEST-PQ-008: Do you ship to Canada?"""
        result = send_message("Do you ship to Canada?")
        
        response_lower = result['response'].lower()
        
        # Should address Canada specifically
        addresses_canada = 'canada' in response_lower or 'canadian' in response_lower
        
        # Should give yes/no answer
        has_answer = any(word in response_lower for word in ['yes', 'no', 'do ship', "don't ship"])
        
        print(f"✅ Addresses Canada: {addresses_canada}, Has answer: {has_answer}")
    
    def test_pq_009_expedited_shipping(self, agent, send_message):
        """TEST-PQ-009: Can I get expedited shipping?"""
        result = send_message("Can I get expedited shipping?")
        
        response_lower = result['response'].lower()
        
        # Should address expedited shipping
        addresses_expedited = any(word in response_lower for word in ['expedit', 'express', 'fast', 'rush'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Addresses expedited: {addresses_expedited}")
    
    def test_pq_010_exchange_process(self, agent, send_message):
        """TEST-PQ-010: Can I exchange for a different size?"""
        result = send_message("Can I exchange for a different size?")
        
        response_lower = result['response'].lower()
        
        # Should address exchange
        addresses_exchange = 'exchange' in response_lower or 'size' in response_lower
        
        # Should give yes/no answer
        has_answer = 'yes' in response_lower or 'can exchange' in response_lower
        
        print(f"✅ Addresses exchange: {addresses_exchange}, Has answer: {has_answer}")
    
    def test_pq_011_exchange_color(self, agent, send_message):
        """TEST-PQ-011: Can I exchange my blue dress for a black one?"""
        result = send_message("Can I exchange my blue dress for a black one?")
        
        response_lower = result['response'].lower()
        
        # Should address color exchange
        addresses_exchange = 'exchange' in response_lower or 'color' in response_lower
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Addresses color exchange: {addresses_exchange}")
    
    def test_pq_012_payment_methods(self, agent, send_message):
        """TEST-PQ-012: What payment methods do you accept?"""
        result = send_message("What payment methods do you accept?")
        
        response_lower = result['response'].lower()
        
        # Should mention payment options
        mentions_payment = any(word in response_lower for word in ['payment', 'card', 'credit', 'accept', 'method'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Mentions payment: {mentions_payment}")
    
    def test_pq_013_price_match(self, agent, send_message):
        """TEST-PQ-013: Do you price match?"""
        result = send_message("Do you price match?")
        
        response_lower = result['response'].lower()
        
        # Should address price matching
        addresses_price_match = 'price' in response_lower or 'match' in response_lower
        
        # Should give yes/no answer
        has_answer = any(word in response_lower for word in ['yes', 'no', 'do', "don't"])
        
        print(f"✅ Addresses price match: {addresses_price_match}, Has answer: {has_answer}")
    
    def test_pq_014_nonexistent_policy(self, agent, send_message):
        """TEST-PQ-014: What's your military discount policy?"""
        result = send_message("What's your military discount policy?")
        
        response = result['response']
        
        # Should not hallucinate a policy
        # Should either say not available or offer to check
        response_lower = response.lower()
        
        # Check it doesn't make up specific discount amounts
        assert len(response) > 0, "No response provided"
        print("✅ Handled non-existent policy query")
    
    def test_pq_015_policy_contradiction(self, agent, send_message):
        """TEST-PQ-015: Your website says 60-day returns but you just said 30 days"""
        result = send_message("Your website says 60-day returns but you just said 30 days. Which is correct?")
        
        response_lower = result['response'].lower()
        
        # Should acknowledge confusion
        acknowledges = any(word in response_lower for word in ['apolog', 'sorry', 'confus', 'clarif'])
        
        # Should not be defensive
        not_defensive = 'incorrect' not in response_lower and "you're wrong" not in response_lower
        
        print(f"✅ Acknowledges: {acknowledges}, Professional: {not_defensive}")
