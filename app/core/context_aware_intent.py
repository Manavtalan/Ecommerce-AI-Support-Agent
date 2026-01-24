# context_aware_intent.py
"""
Context-Aware Intent Resolution
Determines if user message is a follow-up question or new query by analyzing conversation context.
"""

from typing import Tuple
from intent import detect_intent
import re


class ContextAwareIntentResolver:
    """
    Resolves user intent by combining current message with conversation context.
    Prevents robotic "which order" loops and enables natural conversation flow.
    """
    
    # Words that typically indicate follow-up questions
    FOLLOW_UP_INDICATORS = [
        "why", "when", "how", "where", "what",
        "it", "that", "this", "them", "those",
        "and", "also", "what about", "how about",
        "still", "yet", "now", "already", "though"
    ]
    
    # Keywords that indicate order-related questions
    ORDER_RELATED_KEYWORDS = [
        "late", "delayed", "arrive", "delivery", "shipping",
        "track", "status", "update", "progress", "eta",
        "receive", "get", "coming", "shipped", "courier"
    ]
    
    @staticmethod
    def is_follow_up_question(message: str) -> bool:
        """
        Determine if message is a follow-up that needs context.
        
        A follow-up question:
        - Doesn't specify a new order number
        - Uses pronouns or context references
        - Asks about timing/delivery without specifying which order
        
        Args:
            message: User's current message
            
        Returns:
            True if this appears to be a follow-up question
        """
        message_lower = message.lower().strip()
        
        # Check if message has a specific order number
        has_order_number = bool(re.search(r'\b\d{4,6}\b', message_lower))
        
        # If it has an order number, it's NOT a follow-up (it's specifying which order)
        if has_order_number:
            return False
        
        # Check for follow-up indicators at start (question words)
        for indicator in ContextAwareIntentResolver.FOLLOW_UP_INDICATORS:
            if message_lower.startswith(indicator):
                return True
        
        # Check for explicit context references
        context_references = ["this order", "that order", "my order", "the order"]
        if any(ref in message_lower for ref in context_references):
            return True
        
        # Check for timing questions without specifying which order
        timing_questions = [
            "when will", "when can", "when do", "when does",
            "how long", "how soon", "what time", "by when"
        ]
        
        if any(phrase in message_lower for phrase in timing_questions):
            # Asking "when" but no order number = follow-up
            return True
        
        # Check for delivery/arrival questions (common follow-ups)
        arrival_keywords = ["eta", "arrive", "arrival", "reach", "receive", "get it"]
        if any(word in message_lower for word in arrival_keywords):
            return True
        
        # Check for pronouns in short messages (e.g., "track it", "where is it")
        if len(message.split()) <= 8:
            pronouns = ["it", "that", "this"]
            message_words = message_lower.split()
            if any(pronoun in message_words for pronoun in pronouns):
                return True
        
        return False
    
    @staticmethod
    def can_use_order_context(message: str, context) -> bool:
        """
        Determine if it's safe to use order_id from conversation context.
        
        Safe to use context if:
        - We have a stored order_id
        - Last intent was order-related
        - Message is asking about order-related things
        - No NEW different order number is mentioned
        
        Args:
            message: User's current message
            context: ConversationContext object
            
        Returns:
            True if we should use the stored order_id from context
        """
        
        # Must have order context stored
        if not context.last_order_id:
            return False
        
        # Last intent should be order-related
        if context.last_intent not in ["order_status", "order_status_followup", "shipping"]:
            return False
        
        # Check if message has a NEW order number
        new_order_match = re.search(r'\b\d{4,6}\b', message.lower())
        if new_order_match:
            new_order_id = new_order_match.group()
            # If different order number mentioned, don't use context
            if new_order_id != context.last_order_id:
                return False
        
        # Message should be asking about order-related things
        message_lower = message.lower()
        is_order_related = any(
            keyword in message_lower 
            for keyword in ContextAwareIntentResolver.ORDER_RELATED_KEYWORDS
        )
        
        return is_order_related
    
    @staticmethod
    def resolve_with_context(message: str, context) -> Tuple[str, bool]:
        """
        Resolve intent using conversation context if applicable.
        
        Decision logic:
        1. Try standard intent detection first
        2. If intent is clearly NOT order-related, use it
        3. Check if this is a follow-up question
        4. If follow-up AND we have context, use context
        5. Otherwise use base intent (new query)
        
        Args:
            message: User's current message
            context: ConversationContext object
            
        Returns:
            Tuple of (resolved_intent, used_context_flag)
            - resolved_intent: The final intent classification
            - used_context_flag: Whether context was used in resolution
        """
        
        # Step 1: Try standard intent detection first
        base_intent = detect_intent(message)
        
        # Step 2: If intent is clearly NOT order-related, use it immediately
        # These intents should never be overridden by context
        non_contextual_intents = ["cancellation", "returns", "greeting"]
        if base_intent in non_contextual_intents:
            return base_intent, False
        
        # Step 3: Check if this is a follow-up question
        is_followup = ContextAwareIntentResolver.is_follow_up_question(message)
        
        # Step 4: If it's a follow-up AND we have usable context, apply it
        if is_followup and ContextAwareIntentResolver.can_use_order_context(message, context):
            return "order_status_followup", True
        
        # Step 5: Use base intent (this is a new query, not a follow-up)
        return base_intent, False
