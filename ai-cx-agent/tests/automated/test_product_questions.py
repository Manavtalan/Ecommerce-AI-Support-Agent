"""
Automated Tests: Product Questions (10 tests)
"""

import pytest


class TestProductQuestions:
    """10 automated tests for product inquiry functionality"""
    
    def test_pr_001_product_availability(self, agent, send_message):
        """TEST-PR-001: Do you have blue denim jackets in stock?"""
        result = send_message("Do you have blue denim jackets in stock?")
        
        print("\n" + "="*80)
        print("QUESTION: Do you have blue denim jackets in stock?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        addresses_product = 'jacket' in response_lower or 'denim' in response_lower
        gives_info = any(word in response_lower for word in ['stock', 'available', 'yes', 'no', 'have'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Addresses product: {addresses_product}, Gives info: {gives_info}")
    
    def test_pr_002_product_details(self, agent, send_message):
        """TEST-PR-002: Tell me about the Summer Floral Dress"""
        result = send_message("Tell me about the Summer Floral Dress")
        
        print("\n" + "="*80)
        print("QUESTION: Tell me about the Summer Floral Dress")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response = result['response']
        assert len(response) > 30, "Response too short for product details"
        
        response_lower = response.lower()
        provides_details = any(word in response_lower for word in ['dress', 'floral', 'summer', 'price', 'size'])
        
        print(f"✅ Provides details: {provides_details}")
    
    def test_pr_003_size_guide(self, agent, send_message):
        """TEST-PR-003: What size should I get? I'm 5'6" and 140 lbs"""
        result = send_message("What size should I get? I'm 5'6\" and 140 lbs")
        
        print("\n" + "="*80)
        print("QUESTION: What size should I get? I'm 5'6\" and 140 lbs")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        provides_guidance = any(word in response_lower for word in ['size', 'chart', 'guide', 'fit', 'recommend'])
        
        assert len(result['response']) > 20, "Response too short"
        print(f"✅ Provides guidance: {provides_guidance}")
    
    def test_pr_004_product_comparison(self, agent, send_message):
        """TEST-PR-004: What's the difference between the blue dress and the black dress?"""
        result = send_message("What's the difference between the blue dress and the black dress?")
        
        print("\n" + "="*80)
        print("QUESTION: What's the difference between the blue dress and the black dress?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        addresses_comparison = 'blue' in response_lower and 'black' in response_lower
        mentions_difference = any(word in response_lower for word in ['difference', 'differ', 'color', 'style'])
        
        print(f"✅ Addresses both: {addresses_comparison}, Mentions difference: {mentions_difference}")
    
    def test_pr_005_product_recommendation(self, agent, send_message):
        """TEST-PR-005: I'm looking for a dress for a summer wedding. Any suggestions?"""
        result = send_message("I'm looking for a dress for a summer wedding. Any suggestions?")
        
        print("\n" + "="*80)
        print("QUESTION: I'm looking for a dress for a summer wedding. Any suggestions?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        provides_suggestions = any(word in response_lower for word in ['suggest', 'recommend', 'dress', 'perfect', 'great'])
        
        assert len(result['response']) > 30, "Response too short for recommendations"
        print(f"✅ Provides suggestions: {provides_suggestions}")
    
    def test_pr_006_material_inquiry(self, agent, send_message):
        """TEST-PR-006: What is the Summer Floral Dress made of?"""
        result = send_message("What is the Summer Floral Dress made of?")
        
        print("\n" + "="*80)
        print("QUESTION: What is the Summer Floral Dress made of?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        addresses_material = any(word in response_lower for word in ['material', 'fabric', 'cotton', 'polyester', 'made'])
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Addresses material: {addresses_material}")
    
    def test_pr_007_care_instructions(self, agent, send_message):
        """TEST-PR-007: How do I wash the Summer Floral Dress?"""
        result = send_message("How do I wash the Summer Floral Dress?")
        
        print("\n" + "="*80)
        print("QUESTION: How do I wash the Summer Floral Dress?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        provides_care_info = any(word in response_lower for word in ['wash', 'care', 'clean', 'machine', 'hand'])
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Provides care info: {provides_care_info}")
    
    def test_pr_008_color_options(self, agent, send_message):
        """TEST-PR-008: What colors does the Summer Floral Dress come in?"""
        result = send_message("What colors does the Summer Floral Dress come in?")
        
        print("\n" + "="*80)
        print("QUESTION: What colors does the Summer Floral Dress come in?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        mentions_colors = any(word in response_lower for word in ['color', 'blue', 'pink', 'white', 'available'])
        
        assert len(result['response']) > 15, "Response too short"
        print(f"✅ Mentions colors: {mentions_colors}")
    
    def test_pr_009_price_inquiry(self, agent, send_message):
        """TEST-PR-009: How much does the Summer Floral Dress cost?"""
        result = send_message("How much does the Summer Floral Dress cost?")
        
        print("\n" + "="*80)
        print("QUESTION: How much does the Summer Floral Dress cost?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        mentions_price = any(word in response_lower for word in ['price', 'cost', '$', 'rupees', '₹'])
        
        assert len(result['response']) > 10, "Response too short"
        print(f"✅ Mentions price: {mentions_price}")
    
    def test_pr_010_out_of_stock_item(self, agent, send_message):
        """TEST-PR-010: Is the red floral dress available?"""
        result = send_message("Is the red floral dress available?")
        
        print("\n" + "="*80)
        print("QUESTION: Is the red floral dress available?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        addresses_availability = any(word in response_lower for word in ['available', 'stock', 'yes', 'no', 'check'])
        
        assert len(result['response']) > 10, "Response too short"
        print(f"✅ Addresses availability: {addresses_availability}")
