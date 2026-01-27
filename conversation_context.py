
# conversation_context.py
"""
Conversation Context Manager
Manages conversation state and memory within a single customer session.
"""

from datetime import datetime
from typing import Optional
from conversation_state import ActiveTopic, NO_TOPIC


class ConversationContext:
    """
    Manages short-term conversation context for natural interaction flow.
    Tracks current intent, order focus, and conversation history.
    """
    
    def __init__(self):
        """Initialize empty context for new conversation"""
        # NEW: Semantic conversational state
        self.active_topic = NO_TOPIC

        # OLD: Keep existing state (temporary)
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
    
# === NEW: Semantic Topic Management ===

    def set_active_topic(self, topic: ActiveTopic) -> None:
        """
        Set the current conversational topic.
        This is the ONLY way to change focus.
        """
        if not isinstance(topic, ActiveTopic):
            raise TypeError("Must provide ActiveTopic instance")
        self.active_topic = topic

    def get_active_topic(self) -> ActiveTopic:
        """Get current topic (read-only)"""
        return self.active_topic

    def has_active_topic(self) -> bool:
        """Is there an active conversational topic?"""
        return self.active_topic.is_active()

    def clear_topic(self) -> None:
        """Clear active topic"""
        self.active_topic = NO_TOPIC

    def get_order_id_semantic(self):
        """
        Get order_id from semantic topic.
        Returns None if not discussing an order.
        """
        if self.active_topic.is_order_topic():
            return self.active_topic.entity_id
        return None

    def __str__(self) -> str:
        """Human-readable context for debugging"""
        return (
        f"ConversationContext(\n"
        f"  active_topic={self.active_topic},\n"
        f"  turns={self.conversation_turns},\n"
        f"  [OLD] last_order_id={self.last_order_id}, last_intent={self.last_intent}\n"
        f")"
    )
