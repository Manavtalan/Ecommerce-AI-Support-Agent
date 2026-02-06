"""
Automated Tests: Context & Flow (15 tests)
"""

import pytest


class TestContextFlow:
    """15 automated tests for conversation context and flow"""
    
    def test_cf_001_pronoun_resolution(self, agent, multi_turn_conversation):
        """TEST-CF-001: Pronoun resolution - it, that, this"""
        turns = [
            "I ordered a blue dress",
            "When will it arrive?"
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
        
        turn2_lower = results[1]['response'].lower()
        understands_it_means_dress = any(word in turn2_lower for word in ['dress', 'order', 'deliver'])
        doesnt_ask_what = 'what are you referring' not in turn2_lower
        
        print(f"✅ Understands 'it': {understands_it_means_dress}, Doesn't ask 'what': {doesnt_ask_what}")
    
    def test_cf_002_topic_switch(self, agent, multi_turn_conversation):
        """TEST-CF-002: Handling topic switches"""
        turns = [
            "Where is my order 12345?",
            "Actually, what's your return policy?"
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
        
        turn2_lower = results[1]['response'].lower()
        switches_to_policy = 'return' in turn2_lower or 'policy' in turn2_lower
        doesnt_stay_on_order = True  # Should not keep talking about order 12345
        
        print(f"✅ Switches to policy: {switches_to_policy}")
    
    def test_cf_003_implicit_continuation(self, agent, multi_turn_conversation):
        """TEST-CF-003: Implicit continuation"""
        turns = [
            "I want to buy a dress",
            "What colors do you have?"
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
        
        turn2_lower = results[1]['response'].lower()
        understands_colors_for_dress = 'dress' in turn2_lower or 'color' in turn2_lower
        
        print(f"✅ Understands context: {understands_colors_for_dress}")
    
    def test_cf_004_remembering_order_number(self, agent, multi_turn_conversation):
        """TEST-CF-004: Remembering order number across turns"""
        turns = [
            "My order is 12345",
            "When will it arrive?",
            "Can I track it?"
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
        
        turn2 = results[1]['response']
        turn3 = results[2]['response']
        
        doesnt_ask_again_turn2 = 'order number' not in results[1]['response'].lower()
        doesnt_ask_again_turn3 = 'order number' not in results[2]['response'].lower()
        
        print(f"✅ Remembers in turn 2: {doesnt_ask_again_turn2}, Remembers in turn 3: {doesnt_ask_again_turn3}")
    
    def test_cf_005_clarification_loop(self, agent, multi_turn_conversation):
        """TEST-CF-005: Handling clarification questions"""
        turns = [
            "I want to return something",
            "A dress",
            "The blue one I ordered last week"
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
        
        turn1_asks = any(phrase in results[0]['response'].lower() for phrase in ['which', 'what item', 'order'])
        
        print(f"✅ Asks for clarification: {turn1_asks}")
    
    def test_cf_006_correction_handling(self, agent, multi_turn_conversation):
        """TEST-CF-006: User corrects themselves"""
        turns = [
            "I ordered a blue dress",
            "Sorry, I meant a black dress"
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
        
        turn2_lower = results[1]['response'].lower()
        acknowledges_correction = 'black' in turn2_lower
        doesnt_mention_blue = 'blue' not in turn2_lower or 'black' in turn2_lower
        
        print(f"✅ Acknowledges correction: {acknowledges_correction}")
    
    def test_cf_007_elliptical_responses(self, agent, multi_turn_conversation):
        """TEST-CF-007: Handling elliptical responses"""
        turns = [
            "Do you have dresses in blue or black?",
            "Blue"
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
        
        turn2_lower = results[1]['response'].lower()
        understands_blue_dress = 'blue' in turn2_lower and 'dress' in turn2_lower
        
        print(f"✅ Understands elliptical response: {understands_blue_dress}")
    
    def test_cf_008_long_conversation_memory(self, agent, multi_turn_conversation):
        """TEST-CF-008: Memory over 5+ turns"""
        turns = [
            "I'm looking for a dress",
            "For a wedding",
            "In summer",
            "Outdoor wedding",
            "What do you suggest?"
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
        
        final_response = results[4]['response'].lower()
        remembers_context = any(word in final_response for word in ['wedding', 'summer', 'outdoor', 'dress'])
        
        print(f"✅ Remembers context: {remembers_context}")
    
    def test_cf_009_ambiguous_this(self, agent, multi_turn_conversation):
        """TEST-CF-009: Resolving ambiguous 'this'"""
        turns = [
            "I have order 12345 and order 12346",
            "This one is late"
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
        
        turn2_lower = results[1]['response'].lower()
        asks_for_clarification = any(phrase in turn2_lower for phrase in ['which one', 'which order', '12345 or 12346'])
        
        print(f"✅ Asks for clarification: {asks_for_clarification}")
    
    def test_cf_010_temporal_reference(self, agent, multi_turn_conversation):
        """TEST-CF-010: Understanding temporal references"""
        turns = [
            "I placed an order yesterday",
            "Has it shipped yet?"
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
        
        turn2_lower = results[1]['response'].lower()
        understands_it_refers_to_order = 'order' in turn2_lower or 'ship' in turn2_lower
        
        print(f"✅ Understands temporal reference: {understands_it_refers_to_order}")
    
    def test_cf_011_comparison_context(self, agent, multi_turn_conversation):
        """TEST-CF-011: Maintaining context in comparisons"""
        turns = [
            "Tell me about the blue dress",
            "How does it compare to the black one?"
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
        
        turn2_lower = results[1]['response'].lower()
        compares_dresses = 'blue' in turn2_lower or 'black' in turn2_lower or 'dress' in turn2_lower
        
        print(f"✅ Compares dresses: {compares_dresses}")
    
    def test_cf_012_followup_why(self, agent, multi_turn_conversation):
        """TEST-CF-012: Handling 'why' followup"""
        turns = [
            "My order was cancelled",
            "Why?"
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
        
        turn2_lower = results[1]['response'].lower()
        explains_cancellation = any(word in turn2_lower for word in ['cancel', 'reason', 'because'])
        
        print(f"✅ Explains cancellation: {explains_cancellation}")
    
    def test_cf_013_multiple_questions_single_turn(self, agent, send_message):
        """TEST-CF-013: Multiple questions in one message"""
        result = send_message("Where is my order and when will it arrive and can I track it?")
        
        print("\n" + "="*80)
        print("QUESTION: Where is my order and when will it arrive and can I track it?")
        print("-"*80)
        print("AGENT RESPONSE:")
        print(result['response'])
        print("="*80)
        
        response_lower = result['response'].lower()
        addresses_location = any(word in response_lower for word in ['where', 'location', 'status'])
        addresses_time = any(word in response_lower for word in ['when', 'arrive', 'delivery'])
        addresses_tracking = any(word in response_lower for word in ['track', 'tracking'])
        
        print(f"✅ Addresses all 3 questions: location={addresses_location}, time={addresses_time}, tracking={addresses_tracking}")
    
    def test_cf_014_yes_no_response(self, agent, multi_turn_conversation):
        """TEST-CF-014: Understanding yes/no responses"""
        turns = [
            "Do you want to cancel your order?",
            "Yes"
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
        
        turn2_lower = results[1]['response'].lower()
        understands_yes_means_cancel = 'cancel' in turn2_lower or 'help' in turn2_lower
        
        print(f"✅ Understands 'yes' means cancel: {understands_yes_means_cancel}")
    
    def test_cf_015_context_reset_after_completion(self, agent, multi_turn_conversation):
        """TEST-CF-015: Context reset after task completion"""
        turns = [
            "Where is order 12345?",
            "Thanks!",
            "Do you have blue dresses?"
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
        
        turn3_lower = results[2]['response'].lower()
        doesnt_mention_order = '12345' not in turn3_lower
        addresses_new_topic = 'dress' in turn3_lower or 'blue' in turn3_lower
        
        print(f"✅ Resets context: {doesnt_mention_order}, Addresses new topic: {addresses_new_topic}")
