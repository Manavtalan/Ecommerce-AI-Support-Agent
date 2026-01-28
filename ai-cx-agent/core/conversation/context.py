"""
Enhanced Conversation Context
Combines memory (message history) with semantic state (topics, intents)
"""

from typing import Optional, Dict, List
from datetime import datetime
from core.conversation.memory import ConversationMemory
from core.conversation.state import ActiveTopic, TopicType, TopicConfidence


class ConversationContext:
    """
    Manages both conversation memory AND semantic state
    
    This class brings together:
    - ConversationMemory: Stores message history for context retention
    - ActiveTopic: Tracks current conversation topic
    - Metadata: Stores conversation-level information
    """
    
    def __init__(self, max_history: int = 20, max_tokens: int = 4000):
        """
        Initialize conversation context
        
        Args:
            max_history: Maximum messages in memory
            max_tokens: Maximum tokens in memory
        """
        # Memory system (NEW - fixes context loss)
        self.memory = ConversationMemory(
            max_history=max_history,
            max_tokens=max_tokens
        )
        
        # Semantic state tracking (EXISTING)
        self.active_topic: Optional[ActiveTopic] = None
        
        # Conversation metadata
        self.metadata: Dict = {
            "user_name": None,
            "order_id": None,  # Currently discussed order
            "product_id": None,  # Currently discussed product
            "last_emotion": "neutral",
            "escalation_needed": False
        }
        
        # Conversation state flags
        self.is_active = True
        self.session_id: Optional[str] = None
    
    def add_user_message(self, content: str) -> None:
        """
        Add user message to conversation
        
        Args:
            content: User's message
        
        Example:
            context.add_user_message("Where is order 12345?")
        """
        self.memory.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> None:
        """
        Add assistant response to conversation
        
        Args:
            content: Assistant's response
        
        Example:
            context.add_assistant_message("Your order is shipped!")
        """
        self.memory.add_message("assistant", content)
    
    def add_system_message(self, content: str) -> None:
        """
        Add system message to conversation
        
        Args:
            content: System message
        """
        self.memory.add_message("system", content)
    
    def get_messages_for_llm(self, system_prompt: str) -> List[Dict[str, str]]:
        """
        Get formatted messages for LLM API call
        
        Args:
            system_prompt: System prompt to use
        
        Returns:
            Formatted messages ready for OpenAI API
        """
        return self.memory.get_messages_for_llm(system_prompt)
    
    def set_active_topic(
        self,
        topic_type: TopicType,
        confidence: TopicConfidence,
        entity_id: Optional[str] = None,
        reason: str = "user_mentioned"
    ) -> None:
        """
        Set the current conversation topic
        
        Args:
            topic_type: Type of topic (ORDER, POLICY, PRODUCT, etc.)
            confidence: How confident we are
            entity_id: The ID of the entity (order_id, product_id, etc.)
            reason: Why this topic was set
        """
        # Create ActiveTopic with all required arguments
        self.active_topic = ActiveTopic(
            topic_type=topic_type,
            entity_id=entity_id,
            confidence=confidence,
            reason=reason,
            established_at=datetime.now()
        )
    
    def get_active_topic(self) -> Optional[ActiveTopic]:
        """Get current active topic"""
        return self.active_topic
    
    def clear_topic(self) -> None:
        """Clear active topic"""
        self.active_topic = None
    
    def update_metadata(self, key: str, value) -> None:
        """
        Update conversation metadata
        
        Args:
            key: Metadata key
            value: Metadata value
        
        Example:
            context.update_metadata("order_id", "12345")
            context.update_metadata("last_emotion", "frustrated")
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default=None):
        """
        Get metadata value
        
        Args:
            key: Metadata key
            default: Default value if key not found
        
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)
    
    def get_conversation_summary(self) -> Dict:
        """
        Get summary of conversation state
        
        Returns:
            Dictionary with conversation details
        """
        memory_stats = self.memory.get_statistics()
        
        return {
            "message_count": memory_stats["current_message_count"],
            "token_count": memory_stats["current_token_count"],
            "active_topic": self.active_topic.topic_type.value if self.active_topic else None,
            "topic_entity_id": self.active_topic.entity_id if self.active_topic else None,
            "order_id": self.metadata.get("order_id"),
            "last_emotion": self.metadata.get("last_emotion"),
            "escalation_needed": self.metadata.get("escalation_needed"),
            "is_active": self.is_active,
            "conversation_age_seconds": memory_stats["conversation_age_seconds"]
        }
    
    def clear(self) -> None:
        """
        Clear conversation context (start fresh)
        """
        self.memory.clear()
        self.active_topic = None
        self.metadata = {
            "user_name": None,
            "order_id": None,
            "product_id": None,
            "last_emotion": "neutral",
            "escalation_needed": False
        }
        self.is_active = True
    
    def get_recent_messages(self, n: int = 5) -> List[Dict]:
        """
        Get recent messages
        
        Args:
            n: Number of recent messages
        
        Returns:
            List of recent messages
        """
        return self.memory.get_recent_messages(n)
    
    def is_approaching_token_limit(self) -> bool:
        """Check if approaching token limit"""
        return self.memory.is_approaching_limit()
    
    def get_context_window_usage(self) -> Dict:
        """Get detailed token usage information"""
        return self.memory.get_context_window_usage()
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        topic = self.active_topic.topic_type.value if self.active_topic else "none"
        return f"ConversationContext(messages={len(self.memory)}, topic={topic})"
    
    def __len__(self) -> int:
        """Get number of messages"""
        return len(self.memory)


# Helper function to create context
def create_context(max_history: int = 20, max_tokens: int = 4000) -> ConversationContext:
    """
    Factory function to create ConversationContext
    
    Args:
        max_history: Max messages to keep
        max_tokens: Max tokens to keep
    
    Returns:
        New ConversationContext instance
    """
    return ConversationContext(max_history=max_history, max_tokens=max_tokens)
