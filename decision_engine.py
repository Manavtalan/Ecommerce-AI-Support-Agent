# decision_engine.py
"""
Golden Decision Layer - Single Source of Truth
Controls ALL conversation flow decisions with deterministic logic.
"""

from typing import Tuple, Optional
from conversation_context import ConversationContext
import re


class DecisionEngine:
    """
    Central authority for all conversation decisions.
    Replaces scattered if-else logic with one authoritative function.
    """
    
    # Frustration keywords
    FRUSTRATION_KEYWORDS = [
        "why aren't you", "not helping", "frustrating", "frustrated",
        "you keep asking", "asked already", "told you", "stop asking",
        "useless", "waste of time", "again and again"
    ]
    
    # Context reset triggers (explicit only)
    EXPLICIT_RESET_TRIGGERS = [
        "another order", "different order", "new order",
        "different issue", "new problem", "something else"
    ]
    
    @staticmethod
    def decide_order_reference(
        user_input: str,
        context: ConversationContext,
        detected_intent: str
    ) -> dict:
        """
        THE GOLDEN DECISION FUNCTION
        
        Decides:
        - Should we use context.last_order_id?
        - Should we ask for order_id?
        - Is this a follow-up or new query?
        - Should we escalate?
        - Should we reset context?
        
        Returns decision dict with action plan.
        """
        
        decision = {
            "action": None,  # 'use_context', 'ask_order', 'new_order', 'escalate', 'frustration'
            "order_id": None,
            "reason": None,
            "response_type": None
        }
        
        # Extract order number from input
        order_match = re.search(r'\b(\d{4,6})\b', user_input.lower())
        explicit_order_id = order_match.group(1) if order_match else None
        
        # Check for frustration FIRST (highest priority)
        if DecisionEngine.is_frustrated(user_input):
            decision["action"] = "frustration"
            decision["reason"] = "User showing frustration"
            decision["order_id"] = context.last_order_id  # Keep context!
            return decision
        
        # Check for explicit escalation
        if detected_intent in ["cancellation", "refund_request"]:
            decision["action"] = "escalate"
            decision["reason"] = f"Intent: {detected_intent}"
            return decision
        
        # Check for explicit context reset
        if DecisionEngine.should_reset_explicitly(user_input):
            decision["action"] = "reset_then_proceed"
            decision["reason"] = "User explicitly changed topic"
            return decision
        
        # GOLDEN RULE 1: If context exists + no new order mentioned = USE CONTEXT
        if context.last_order_id and not explicit_order_id:
            if DecisionEngine.is_order_related_query(user_input, detected_intent):
                decision["action"] = "use_context"
                decision["order_id"] = context.last_order_id
                decision["reason"] = "Order in context, query is order-related"
                decision["response_type"] = "followup"
                return decision
        
        # GOLDEN RULE 2: User provided new order number = USE NEW ORDER
        if explicit_order_id:
            decision["action"] = "new_order"
            decision["order_id"] = explicit_order_id
            decision["reason"] = "User provided order number"
            decision["response_type"] = "new_query"
            return decision
        
        # GOLDEN RULE 3: Order query but no order in context = ASK FOR ORDER
        if detected_intent == "order_status":
            decision["action"] = "ask_order"
            decision["reason"] = "Order query without context or explicit order"
            return decision
        
        # GOLDEN RULE 4: Everything else = LLM fallback
        decision["action"] = "llm_fallback"
        decision["reason"] = f"General query, intent: {detected_intent}"
        return decision
    
    @staticmethod
    def is_order_related_query(user_input: str, detected_intent: str) -> bool:
        """
        Determine if query is about orders/shipping/delivery.
        """
        order_keywords = [
            "order", "delivery", "shipping", "arrive", "track",
            "eta", "status", "delayed", "late", "reach", "receive",
            "package", "courier", "shipment"
        ]
        
        # Intent-based
        if detected_intent in ["order_status", "shipping"]:
            return True
        
        # Keyword-based
        message_lower = user_input.lower()
        if any(keyword in message_lower for keyword in order_keywords):
            return True
        
        # Pronoun-based (it, this, that)
        pronouns = ["it", "this", "that"]
        if any(pronoun in message_lower.split() for pronoun in pronouns):
            return True
        
        return False
    
    @staticmethod
    def is_frustrated(user_input: str) -> bool:
        """Detect frustration keywords."""
        message_lower = user_input.lower()
        return any(keyword in message_lower for keyword in DecisionEngine.FRUSTRATION_KEYWORDS)
    
    @staticmethod
    def should_reset_explicitly(user_input: str) -> bool:
        """Check if user explicitly wants to change topic."""
        message_lower = user_input.lower()
        return any(trigger in message_lower for trigger in DecisionEngine.EXPLICIT_RESET_TRIGGERS)
    
    @staticmethod
    def get_frustration_response(context: ConversationContext) -> str:
        """
        Generate empathetic response to frustration.
        NEVER ask for order ID if it exists in context.
        """
        if context.last_order_id:
            return (
                f"I apologize for the confusion. I have your order #{context.last_order_id} "
                f"right here. Let me help you with that."
            )
        else:
            return (
                "I apologize for the frustration. I'm here to help. "
                "Could you share your order number so I can assist you right away?"
            )