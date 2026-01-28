"""
Conversation Memory System
Maintains conversation history for context retention across multiple turns
"""

from typing import List, Dict, Optional
from datetime import datetime


class ConversationMemory:
    """
    Stores and manages conversation history
    
    This is the CORE component that fixes context loss:
    - Stores all messages (user + assistant)
    - Maintains chronological order
    - Formats messages for LLM API calls
    - Handles token limits via summarization
    """
    
    def __init__(self, max_history: int = 20, max_tokens: int = 4000):
        """
        Initialize conversation memory
        
        Args:
            max_history: Maximum number of messages to keep (default: 20)
            max_tokens: Approximate max tokens for conversation history (default: 4000)
                       Leave room for system prompt and response
        """
        self.messages: List[Dict[str, str]] = []
        self.max_history = max_history
        self.max_tokens = max_tokens
        self.created_at = datetime.now()
        
        # Statistics for monitoring
        self.total_messages_added = 0
        self.total_summarizations = 0
        self.total_tokens_estimated = 0
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to conversation history
        
        Args:
            role: 'user' or 'assistant' or 'system'
            content: The message content
        
        Example:
            memory.add_message("user", "Where is order 12345?")
            memory.add_message("assistant", "Your order is shipped")
        """
        # Validate role
        if role not in ["user", "assistant", "system"]:
            raise ValueError(f"Invalid role: {role}. Must be 'user', 'assistant', or 'system'")
        
        # Add message
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "tokens": self._estimate_tokens(content)
        }
        
        self.messages.append(message)
        self.total_messages_added += 1
        self.total_tokens_estimated += message["tokens"]
        
        # Check if we need to trim by count
        if len(self.messages) > self.max_history:
            self._trim_history()
        
        # Check if we need to trim by tokens
        if self._get_total_tokens() > self.max_tokens:
            self._trim_by_tokens()
    
    def get_messages_for_llm(self, system_prompt: str) -> List[Dict[str, str]]:
        """
        Format messages for OpenAI API call
        
        Args:
            system_prompt: The system prompt to prepend
        
        Returns:
            List of messages in OpenAI format
        
        Example:
            messages = memory.get_messages_for_llm("You are a helpful agent")
            # Returns:
            # [
            #   {"role": "system", "content": "You are a helpful agent"},
            #   {"role": "user", "content": "Where is order 12345?"},
            #   {"role": "assistant", "content": "Your order is shipped"},
            #   ...
            # ]
        """
        # Start with system prompt
        formatted_messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history (without timestamps and token counts)
        for msg in self.messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return formatted_messages
    
    def get_recent_messages(self, n: int = 5) -> List[Dict[str, str]]:
        """
        Get the N most recent messages
        
        Args:
            n: Number of recent messages to return
        
        Returns:
            List of recent messages
        """
        return self.messages[-n:] if n <= len(self.messages) else self.messages
    
    def clear(self) -> None:
        """
        Clear all conversation history
        
        Use this when starting a new conversation
        """
        self.messages = []
        self.created_at = datetime.now()
        self.total_tokens_estimated = 0
    
    def get_message_count(self) -> int:
        """Get total number of messages in history"""
        return len(self.messages)
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Simple estimation: ~4 characters per token
        This is approximate but good enough for our purposes
        
        For more accuracy, could use tiktoken library, but this adds dependency
        
        Args:
            text: The text to estimate
        
        Returns:
            Estimated token count
        """
        # Simple estimation: 1 token ≈ 4 characters
        # This is conservative (slightly overestimates)
        return len(text) // 4 + 1
    
    def _get_total_tokens(self) -> int:
        """
        Get total estimated tokens for all messages
        
        Returns:
            Total token count
        """
        return sum(msg.get("tokens", 0) for msg in self.messages)
    
    def _trim_history(self) -> None:
        """
        Trim history when it exceeds max_history
        
        Strategy: Keep most recent messages, remove oldest
        """
        if len(self.messages) > self.max_history:
            # Keep only the most recent max_history messages
            messages_to_remove = len(self.messages) - self.max_history
            self.messages = self.messages[messages_to_remove:]
    
    def _trim_by_tokens(self) -> None:
        """
        Trim history when token count exceeds max_tokens
        
        Strategy: Remove oldest messages until under limit
        Keep at least 2 messages (1 user + 1 assistant pair)
        """
        while self._get_total_tokens() > self.max_tokens and len(self.messages) > 2:
            # Remove oldest message
            removed = self.messages.pop(0)
            self.total_summarizations += 1
    
    def get_statistics(self) -> Dict:
        """
        Get memory statistics for monitoring
        
        Returns:
            Dictionary with stats
        """
        return {
            "current_message_count": len(self.messages),
            "current_token_count": self._get_total_tokens(),
            "max_history": self.max_history,
            "max_tokens": self.max_tokens,
            "total_messages_added": self.total_messages_added,
            "total_summarizations": self.total_summarizations,
            "conversation_age_seconds": (datetime.now() - self.created_at).total_seconds(),
            "tokens_per_message_avg": self._get_total_tokens() / len(self.messages) if self.messages else 0
        }
    
    def is_approaching_limit(self, threshold: float = 0.8) -> bool:
        """
        Check if conversation is approaching token limit
        
        Args:
            threshold: Percentage of max_tokens (default: 0.8 = 80%)
        
        Returns:
            True if approaching limit
        """
        current_tokens = self._get_total_tokens()
        return current_tokens > (self.max_tokens * threshold)
    
    def get_context_window_usage(self) -> Dict:
        """
        Get detailed context window usage information
        
        Returns:
            Dictionary with usage details
        """
        current_tokens = self._get_total_tokens()
        return {
            "current_tokens": current_tokens,
            "max_tokens": self.max_tokens,
            "percentage_used": (current_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0,
            "tokens_remaining": self.max_tokens - current_tokens,
            "is_approaching_limit": self.is_approaching_limit()
        }
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        tokens = self._get_total_tokens()
        return f"ConversationMemory(messages={len(self.messages)}, tokens≈{tokens}, max={self.max_history})"
    
    def __len__(self) -> int:
        """Allow len(memory) to get message count"""
        return len(self.messages)


# Helper function to create a new memory instance
def create_memory(max_history: int = 20, max_tokens: int = 4000) -> ConversationMemory:
    """
    Factory function to create a new ConversationMemory instance
    
    Args:
        max_history: Maximum messages to keep
        max_tokens: Maximum tokens to keep
    
    Returns:
        New ConversationMemory instance
    """
    return ConversationMemory(max_history=max_history, max_tokens=max_tokens)
