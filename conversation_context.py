# conversation_context.py
"""
Conversation Context Manager - SIMPLIFIED VERSION
"""

from datetime import datetime
from typing import Optional, Dict, Any

class ConversationContext:
    """Manages conversation state within a single session."""
    
    def __init__(self):
        """Initialize empty context"""
        self.reset()
    
    def reset(self):
        """Clear all context - fresh start"""
        self.last_intent: Optional[str] = None
        self.last_order_id: Optional[str] = None
        self.pending_intent: Optional[str] = None
        self.conversation_turns: int = 0
        self.last_user_message: Optional[str] = None
        self.last_agent_response: Optional[str] = None
        self.context_created_at: datetime = datetime.now()
    
    def update_intent(self, intent: str):
        """Record what the user just asked about"""
        self.last_intent = intent
    
    def update_order_id(self, order_id: str):
        """Store the order number currently in focus"""
        self.last_order_id = order_id
    
    def set_pending_intent(self, intent: str):
        """Mark that we're waiting for user to provide something"""
        self.pending_intent = intent
    
    def clear_pending_intent(self):
        """User provided what we needed, clear the waiting state"""
        self.pending_intent = None
    
    def increment_turn(self):
        """Count conversation messages"""
        self.conversation_turns += 1
    
    def store_user_message(self, message: str):
        """Remember what user just said"""
        self.last_user_message = message
        self.increment_turn()
    
    def store_agent_response(self, response: str):
        """Remember what agent just said"""
        self.last_agent_response = response
    
    def __str__(self) -> str:
        """Human-readable context for debugging"""
        return (
            f"Context(turns={self.conversation_turns}, "
            f"intent={self.last_intent}, "
            f"order={self.last_order_id}, "
            f"pending={self.pending_intent})"
        )