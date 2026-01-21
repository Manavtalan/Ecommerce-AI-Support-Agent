# context_aware_intent.py - COMPLETE WORKING VERSION

from typing import Tuple
from intent import detect_intent

class ContextAwareIntentResolver:
    """Resolves user intent by combining current message with conversation context."""
    
    FOLLOW_UP_INDICATORS = [
        "why", "when", "how", "where", "what",
        "it", "that", "this", "them", "those",
        "and", "also", "what about", "how about",
        "still", "yet", "now", "already"
    ]
    
    ORDER_STATUS_KEYWORDS = [
        "late", "delayed", "arrive", "delivery", "shipping",
        "track", "status", "update", "progress", "eta",
        "receive", "get", "coming"
    ]
    
    @staticmethod
    def is_follow_up_question(message: str) -> bool:
        """Determine if message is a follow-up that needs context."""
        message_lower = message.lower().strip()
        
        # Check if message has a specific order number
        import re
        has_order_number = bool(re.search(r'\b\d{4,6}\b', message_lower))
        
        # If it has an order number, it's NOT a follow-up (it's specifying which order)
        if has_order_number:
            return False
        
        # Check for follow-up indicators at start
        for indicator in ContextAwareIntentResolver.FOLLOW_UP_INDICATORS:
            if message_lower.startswith(indicator):
                return True
        
        # Check for "this order" or "that order" (references current context)
        if "this order" in message_lower or "that order" in message_lower:
            return True
        
        # Check for delivery/timing questions without specifying which order
        timing_questions = [
            "when will", "when can", "when do", "when does",
            "how long", "how soon", "what time"
        ]
        
        if any(phrase in message_lower for phrase in timing_questions):
            # It's asking "when" but no order number = follow-up
            return True
        
        # Check for eta/arrival questions
        if any(word in message_lower for word in ["eta", "arrive", "arrival", "reach", "receive"]):
            return True
        
        # Check for pronouns in short messages
        if len(message.split()) <= 8:
            for pronoun in ["it", "that", "this"]:
                if pronoun in message_lower.split():
                    return True
        
        return False
    
    @staticmethod
    def can_use_order_context(message: str, context) -> bool:
        """Determine if it's safe to use order_id from context."""
        
        # Must have order context
        if not context.last_order_id:
            return False
        
        # Last intent should be order-related
        if context.last_intent not in ["order_status", "order_status_followup", "shipping"]:
            return False
        
        # Check if message has a NEW order number
        import re
        new_order_match = re.search(r'\b\d{4,6}\b', message.lower())
        if new_order_match:
            new_order_id = new_order_match.group()
            if new_order_id != context.last_order_id:
                return False  # Different order number
        
        # Message should be asking about order-related things
        message_lower = message.lower()
        is_order_related = any(
            keyword in message_lower 
            for keyword in ContextAwareIntentResolver.ORDER_STATUS_KEYWORDS
        )
        
        return is_order_related
    
    @staticmethod
    def resolve_with_context(message: str, context) -> Tuple[str, bool]:
        """
        Resolve intent using context if applicable.
        Returns: (resolved_intent, used_context)
        """
        
        # Step 1: Try standard intent detection first
        base_intent = detect_intent(message)
        
        # Step 2: If intent is clearly NOT order-related, use it
        if base_intent in ["cancellation", "returns", "greeting"]:
            return base_intent, False
        
        # Step 3: Check if this is a follow-up question
        is_followup = ContextAwareIntentResolver.is_follow_up_question(message)
        
        # Step 4: If it's a follow-up AND we have context, use it
        if is_followup and ContextAwareIntentResolver.can_use_order_context(message, context):
            return "order_status_followup", True
        
        # Step 5: Use base intent (new query)
        return base_intent, False