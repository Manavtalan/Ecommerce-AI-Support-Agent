# conversation_context.py
"""
Conversation Context Manager
Manages conversation state and memory within a single customer session.
"""

from datetime import datetime
from typing import Optional


class ConversationContext:
    """
    Manages short-term conversation context for natural interaction flow.
    Tracks current intent, order focus, and conversation history.
    """
    
    def __init__(self):
        """Initialize empty context for new conversation"""
        self.reset()
    
    def reset(self):
        """
        Clear all context - fresh start.
        Used after escalations or session end.
        """
        self.last_intent: Optional[str] = None
        self.last_order_id: Optional[str] = None
        self.pending_intent: Optional[str] = None
        self.conversation_turns: int = 0
        self.last_user_message: Optional[str] = None
        self.last_agent_response: Optional[str] = None
        self.context_created_at: datetime = datetime.now()
    
    def update_intent(self, intent: str):
        """
        Record the intent of user's current message.
        Used to understand conversation flow.
        """
        self.last_intent = intent
    
    def update_order_id(self, order_id: str):
        """
        Store the order number currently in focus.
        This makes the order "sticky" for follow-up questions.
        """
        self.last_order_id = order_id
    
    def clear_order_context(self):
        """
        Clear order-specific context only.
        Used when order is invalid or customer switches topics.
        """
        self.last_order_id = None
        # Keep intent history but clear order focus
        if self.last_intent in ["order_status", "order_status_followup"]:
            self.last_intent = None
    
    def set_pending_intent(self, intent: str):
        """
        Mark that we're waiting for user to provide something.
        Example: We asked for order number, waiting for response.
        """
        self.pending_intent = intent
    
    def clear_pending_intent(self):
        """
        User provided what we needed, clear the waiting state.
        """
        self.pending_intent = None
    
    def increment_turn(self):
        """
        Count conversation exchanges.
        Used for analytics and conversation depth tracking.
        """
        self.conversation_turns += 1
    
    def store_user_message(self, message: str):
        """
        Remember what user just said.
        Used for detecting repeated queries and context continuity.
        """
        self.last_user_message = message
        self.increment_turn()
    
    def store_agent_response(self, response: str):
        """
        Remember what agent just said.
        Used for conversation coherence.
        """
        self.last_agent_response = response
    
    def is_repeated_query(self, current_message: str) -> bool:
        """
        Check if user is asking the exact same thing again.
        Helps provide reassurance instead of robotic repetition.
        
        Args:
            current_message: The current user input
            
        Returns:
            True if this is a repeated query, False otherwise
        """
        if not self.last_user_message:
            return False
        
        # Normalize both messages for comparison
        last_normalized = self.last_user_message.lower().strip()
        current_normalized = current_message.lower().strip()
        
        # Check for exact match
        if last_normalized == current_normalized:
            return True
        
        # Check for very similar messages (e.g., "order status" vs "order status?")
        # Remove punctuation and extra spaces
        import re
        last_cleaned = re.sub(r'[^\w\s]', '', last_normalized)
        current_cleaned = re.sub(r'[^\w\s]', '', current_normalized)
        
        if last_cleaned == current_cleaned:
            return True
        
        return False
    
    def __str__(self) -> str:
        """
        Human-readable context for debugging.
        Shows current conversation state at a glance.
        """
        return (
            f"Context("
            f"turns={self.conversation_turns}, "
            f"intent={self.last_intent}, "
            f"order={self.last_order_id}, "
            f"pending={self.pending_intent}"
            f")"
        )
