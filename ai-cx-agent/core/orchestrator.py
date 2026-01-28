"""
Conversation Orchestrator
Coordinates all components for natural conversation flow
"""

from typing import Dict, Tuple, Optional
from core.conversation.context import ConversationContext
from core.emotion.detector import EmotionDetector
from core.llm.composer import LLMResponseComposer


class ConversationOrchestrator:
    """
    Orchestrates the conversation flow by coordinating:
    - Context management (memory)
    - Emotion detection
    - Response generation
    - State tracking
    """
    
    def __init__(
        self,
        brand_voice: Optional[Dict] = None,
        system_prompt: str = "You are a helpful customer support agent."
    ):
        """
        Initialize the orchestrator
        
        Args:
            brand_voice: Brand voice guidelines
            system_prompt: Base system prompt
        """
        # Initialize components
        self.context = ConversationContext()
        self.composer = LLMResponseComposer()
        
        # Store configuration
        self.brand_voice = brand_voice or {}
        self.system_prompt = system_prompt
        
        # Statistics
        self.total_messages_processed = 0
        self.emotions_detected = {
            "frustrated": 0,
            "confused": 0,
            "urgent": 0,
            "positive": 0,
            "neutral": 0
        }
    
    def process_message(
        self,
        user_message: str,
        facts: Optional[Dict] = None,
        constraints: Optional[list] = None
    ) -> Tuple[str, Dict]:
        """
        Process a user message and generate response
        
        Args:
            user_message: The user's message
            facts: Known facts (order details, etc.)
            constraints: What the agent cannot do
        
        Returns:
            Tuple of (response, metadata)
        """
        # Step 1: Add user message to context
        self.context.add_user_message(user_message)
        
        # Step 2: Detect emotion
        emotion, intensity, triggers = EmotionDetector.detect_emotion(user_message)
        
        # Update context metadata
        self.context.update_metadata("last_emotion", emotion)
        
        # Track emotion statistics
        if emotion in self.emotions_detected:
            self.emotions_detected[emotion] += 1
        
        # Step 3: Determine scenario based on emotion and facts
        scenario = self._determine_scenario(emotion, facts)
        
        # Step 4: Prepare facts for composer
        if facts is None:
            facts = {}
        
        # Step 5: Generate response
        response = self.composer.compose_response(
            scenario=scenario,
            facts=facts,
            constraints=constraints or [],
            emotion=emotion,
            brand_voice=self.brand_voice
        )
        
        # Step 6: Add assistant response to context
        self.context.add_assistant_message(response)
        
        # Step 7: Prepare metadata
        metadata = {
            "emotion": emotion,
            "intensity": intensity,
            "scenario": scenario,
            "message_count": len(self.context),
            "token_usage": self.context.get_context_window_usage()
        }
        
        # Update statistics
        self.total_messages_processed += 1
        
        return response, metadata
    
    def _determine_scenario(self, emotion: str, facts: Optional[Dict]) -> str:
        """
        Determine the appropriate scenario based on emotion and context
        
        Args:
            emotion: Detected emotion
            facts: Available facts
        
        Returns:
            Scenario identifier
        """
        # If frustrated, use frustrated customer scenario
        if emotion == "frustrated":
            return "frustrated_customer"
        
        # If has order info and is about delay
        if facts and facts.get("status") == "delayed":
            return "delay_explanation"
        
        # If has order info (standard query)
        if facts and "order_id" in facts:
            return "order_status_simple"
        
        # If asking about policy
        if facts and "policy_type" in facts:
            return "policy_question"
        
        # Default to general query
        return "general_query"
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of current conversation state"""
        return {
            "messages": len(self.context),
            "emotions_detected": self.emotions_detected,
            "total_processed": self.total_messages_processed,
            "context_summary": self.context.get_conversation_summary()
        }
    
    def clear_conversation(self) -> None:
        """Clear conversation and start fresh"""
        self.context.clear()
        self.total_messages_processed = 0
        self.emotions_detected = {
            "frustrated": 0,
            "confused": 0,
            "urgent": 0,
            "positive": 0,
            "neutral": 0
        }
    
    def get_context(self) -> ConversationContext:
        """Get the conversation context"""
        return self.context
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ConversationOrchestrator(messages={len(self.context)}, processed={self.total_messages_processed})"


# Factory function
def create_orchestrator(
    brand_voice: Optional[Dict] = None,
    system_prompt: str = "You are a helpful customer support agent."
) -> ConversationOrchestrator:
    """
    Create a new conversation orchestrator
    
    Args:
        brand_voice: Brand voice guidelines
        system_prompt: System prompt
    
    Returns:
        New ConversationOrchestrator instance
    """
    return ConversationOrchestrator(
        brand_voice=brand_voice,
        system_prompt=system_prompt
    )
