"""
Automated Tests: Performance (8 tests)
"""

import pytest
import time


class TestPerformance:
    """8 automated tests for performance and response times"""
    
    def test_perf_001_simple_query_response_time(self, agent, send_message):
        """TEST-PERF-001: Simple query under 3 seconds"""
        result = send_message("Hello")
        
        print("\n" + "="*80)
        print("QUESTION: Hello")
        print("-"*80)
        print(f"RESPONSE TIME: {result['response_time']:.2f}s")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        assert result['response_time'] < 3.0, f"Simple query too slow: {result['response_time']:.2f}s"
        print(f"✅ Response time: {result['response_time']:.2f}s (< 3s)")
    
    def test_perf_002_order_lookup_response_time(self, agent, send_message):
        """TEST-PERF-002: Order lookup under 5 seconds"""
        result = send_message("Where is my order 12345?")
        
        print("\n" + "="*80)
        print("QUESTION: Where is my order 12345?")
        print("-"*80)
        print(f"RESPONSE TIME: {result['response_time']:.2f}s")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        assert result['response_time'] < 5.0, f"Order lookup too slow: {result['response_time']:.2f}s"
        print(f"✅ Response time: {result['response_time']:.2f}s (< 5s)")
    
    def test_perf_003_policy_query_response_time(self, agent, send_message):
        """TEST-PERF-003: Policy query under 4 seconds"""
        result = send_message("What's your return policy?")
        
        print("\n" + "="*80)
        print("QUESTION: What's your return policy?")
        print("-"*80)
        print(f"RESPONSE TIME: {result['response_time']:.2f}s")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        assert result['response_time'] < 4.0, f"Policy query too slow: {result['response_time']:.2f}s"
        print(f"✅ Response time: {result['response_time']:.2f}s (< 4s)")
    
    def test_perf_004_complex_query_response_time(self, agent, send_message):
        """TEST-PERF-004: Complex query under 6 seconds"""
        result = send_message("I want to return my blue dress from order 12345, exchange it for a different size, and know when the new one will arrive")
        
        print("\n" + "="*80)
        print("QUESTION: Complex multi-part query")
        print("-"*80)
        print(f"RESPONSE TIME: {result['response_time']:.2f}s")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        assert result['response_time'] < 6.0, f"Complex query too slow: {result['response_time']:.2f}s"
        print(f"✅ Response time: {result['response_time']:.2f}s (< 6s)")
    
    def test_perf_005_consecutive_queries(self, agent, send_message):
        """TEST-PERF-005: 5 consecutive queries all under 5 seconds each"""
        queries = [
            "Hello",
            "Where is order 12345?",
            "When will it arrive?",
            "Can I track it?",
            "Thanks"
        ]
        
        print("\n" + "="*80)
        print("CONSECUTIVE QUERIES TEST:")
        print("="*80)
        
        all_fast = True
        for i, query in enumerate(queries, 1):
            result = send_message(query)
            print(f"\nQuery {i}: {query}")
            print(f"Response time: {result['response_time']:.2f}s")
            
            if result['response_time'] >= 5.0:
                all_fast = False
                print(f"❌ Too slow!")
            else:
                print(f"✅ Fast enough")
        
        print("="*80)
        assert all_fast, "Some queries were too slow"
        print(f"✅ All 5 consecutive queries under 5s")
    
    def test_perf_006_multi_turn_performance(self, agent, multi_turn_conversation):
        """TEST-PERF-006: Multi-turn conversation maintains speed"""
        turns = [
            "I need help with my order",
            "It's order 12345",
            "When will it arrive?",
            "Can I change the address?",
            "Thanks!"
        ]
        
        results = multi_turn_conversation(turns)
        
        print("\n" + "="*80)
        print("MULTI-TURN PERFORMANCE:")
        print("="*80)
        
        for r in results:
            print(f"\nTURN {r['turn']}: {r['user_message']}")
            print(f"Response time: {r['response_time']:.2f}s")
        
        print("="*80)
        
        avg_time = sum(r['response_time'] for r in results) / len(results)
        max_time = max(r['response_time'] for r in results)
        
        print(f"\nAverage response time: {avg_time:.2f}s")
        print(f"Max response time: {max_time:.2f}s")
        
        assert avg_time < 4.0, f"Average too slow: {avg_time:.2f}s"
        assert max_time < 6.0, f"Max too slow: {max_time:.2f}s"
        
        print(f"✅ Average: {avg_time:.2f}s, Max: {max_time:.2f}s")
    
    def test_perf_007_response_length_appropriate(self, agent, send_message):
        """TEST-PERF-007: Responses not unnecessarily long"""
        result = send_message("Where is my order?")
        
        print("\n" + "="*80)
        print("QUESTION: Where is my order?")
        print("-"*80)
        print(f"RESPONSE LENGTH: {len(result['response'])} characters")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        # Response should be helpful but not a novel
        response_length = len(result['response'])
        
        assert response_length > 20, "Response too short to be helpful"
        assert response_length < 1000, f"Response unnecessarily long: {response_length} chars"
        
        print(f"✅ Response length: {response_length} chars (20-1000)")
    
    def test_perf_008_no_timeout_on_edge_cases(self, agent, send_message):
        """TEST-PERF-008: Edge cases don't timeout"""
        edge_cases = [
            "",
            "asdfghjkl",
            "😊😊😊",
            "a" * 500,  # Very long single character
            "ORDER ORDER ORDER"
        ]
        
        print("\n" + "="*80)
        print("EDGE CASE TIMEOUT TEST:")
        print("="*80)
        
        all_responded = True
        for i, case in enumerate(edge_cases, 1):
            result = send_message(case)
            display_case = case if len(case) < 50 else case[:47] + "..."
            
            print(f"\nCase {i}: {display_case}")
            print(f"Response time: {result['response_time']:.2f}s")
            print(f"Response length: {len(result['response'])} chars")
            
            if result['response_time'] >= 10.0:
                all_responded = False
                print(f"❌ Timeout!")
            else:
                print(f"✅ No timeout")
        
        print("="*80)
        assert all_responded, "Some edge cases timed out"
        print(f"✅ All edge cases handled without timeout")
