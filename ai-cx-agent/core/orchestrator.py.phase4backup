"""
Conversation Orchestrator
Coordinates all components for natural conversation flow
WITH RAG INTEGRATION for policy questions
"""

from typing import Dict, Tuple, Optional
from core.conversation.context import ConversationContext
from core.emotion.detector import EmotionDetector
from core.llm.composer import LLMResponseComposer
from core.rag.retriever import KnowledgeRetriever


class ConversationOrchestrator:
    """
    Orchestrates the conversation flow by coordinating:
    - Context management (memory)
    - Emotion detection
    - RAG knowledge retrieval (NEW!)
    - Response generation
    - State tracking
    """
    
    def __init__(
        self,
        brand_name: str = "fashionhub",
        brand_voice: Optional[Dict] = None,
        system_prompt: str = "You are a helpful customer support agent."
    ):
        """
        Initialize the orchestrator
        
        Args:
            brand_name: Brand name for RAG retrieval
            brand_voice: Brand voice guidelines
            system_prompt: Base system prompt
        """
        # Initialize components
        self.context = ConversationContext()
        self.composer = LLMResponseComposer()
        
        # NEW: Initialize RAG retriever
        self.brand_name = brand_name
        try:
            self.retriever = KnowledgeRetriever(brand_name)
            self.rag_available = True
            print(f"✅ RAG enabled for {brand_name}")
        except Exception as e:
            print(f"⚠️  RAG not available: {e}")
            self.retriever = None
            self.rag_available = False
        
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
        
        # NEW: RAG statistics
        self.rag_stats = {
            "policy_questions": 0,
            "rag_retrievals": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "escalations": 0
        }
    
    def _is_policy_question(self, message: str) -> bool:
        """
        Detect if message is a policy question
        
        Args:
            message: User message
        
        Returns:
            True if appears to be policy question
        """
        # Policy keywords
        policy_keywords = [
            "policy", "return", "refund", "exchange", "shipping",
            "delivery", "cancel", "cancellation", "free shipping",
            "how long", "how do i", "can i return", "can i cancel",
            "what if", "do you offer", "is there"
        ]
        
        message_lower = message.lower()
        
        # Check for policy keywords
        for keyword in policy_keywords:
            if keyword in message_lower:
                return True
        
        # Check for question patterns
        question_patterns = ["what", "how", "when", "where", "can i", "do you"]
        starts_with_question = any(message_lower.startswith(p) for p in question_patterns)
        
        # No order ID mentioned (likely not order-specific)
        import re
        has_order_id = bool(re.search(r'\b\d{5}\b', message))
        
        return starts_with_question and not has_order_id
    
    def _retrieve_knowledge(self, query: str) -> Optional[Dict]:
        """
        Retrieve relevant knowledge from RAG
        
        Args:
            query: User query
        
        Returns:
            Knowledge retrieval result or None
        """
        if not self.rag_available:
            return None
        
        try:
            self.rag_stats["rag_retrievals"] += 1
            result = self.retriever.retrieve_with_confidence(query)
            
            # Update confidence stats
            if result["confidence"] == "high":
                self.rag_stats["high_confidence"] += 1
            elif result["confidence"] == "medium":
                self.rag_stats["medium_confidence"] += 1
            elif result["confidence"] == "low":
                self.rag_stats["low_confidence"] += 1
            
            if result["action"] == "escalate":
                self.rag_stats["escalations"] += 1
            
            return result
        except Exception as e:
            print(f"⚠️  RAG retrieval error: {e}")
            return None
    
    def _format_rag_context(self, rag_result: Dict) -> str:
        """
        Format RAG results for LLM context
        
        Args:
            rag_result: RAG retrieval result
        
        Returns:
            Formatted context string
        """
        if not rag_result or not rag_result.get("found"):
            return ""
        
        context = "RELEVANT POLICY INFORMATION:\n\n"
        
        # Add retrieved chunks
        for i, result in enumerate(rag_result["results"][:3], 1):
            context += f"[Source {i}: {result['source']}]\n"
            context += f"{result['text']}\n\n"
        
        # Add confidence note
        confidence = rag_result["confidence"]
        if confidence == "medium":
            context += "Note: Use this information but consider mentioning it's based on current policies.\n"
        
        return context
    
    def _format_citation(self, rag_result: Dict) -> str:
        """
        Format citation for response
        
        Args:
            rag_result: RAG retrieval result
        
        Returns:
            Citation string
        """
        if not rag_result or not rag_result.get("results"):
            return ""
        
        sources = list(set([r["source"] for r in rag_result["results"][:3]]))
        
        if len(sources) == 1:
            return f"\n\n[Source: {sources[0]}]"
        else:
            return f"\n\n[Sources: {', '.join(sources)}]"
    
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
        
        # Step 3: Check if this is a policy question
        is_policy_q = self._is_policy_question(user_message)
        rag_result = None
        rag_context = ""
        
        if is_policy_q and self.rag_available:
            self.rag_stats["policy_questions"] += 1
            print(f"🔍 Policy question detected, retrieving from knowledge base...")
            
            # Retrieve from RAG
            rag_result = self._retrieve_knowledge(user_message)
            
            if rag_result and rag_result.get("found"):
                # Format RAG context for LLM
                rag_context = self._format_rag_context(rag_result)
                print(f"   ✅ Retrieved with {rag_result['confidence']} confidence")
        
        # Step 4: Determine scenario
        scenario = self._determine_scenario(emotion, facts, is_policy_q)
        
        # Step 5: Prepare facts for composer
        if facts is None:
            facts = {}
        
        # Add RAG context to facts if available
        if rag_context:
            facts["knowledge_context"] = rag_context
        
        # Step 6: Generate response
        response = self.composer.compose_response(
            scenario=scenario,
            facts=facts,
            constraints=constraints or [],
            emotion=emotion,
            brand_voice=self.brand_voice
        )
        
        # Step 7: Add citation if RAG was used
        if rag_result and rag_result.get("found") and rag_result["confidence"] in ["high", "medium"]:
            citation = self._format_citation(rag_result)
            # Note: Don't append citation to avoid cluttering response
            # LLM will naturally incorporate the knowledge
        
        # Step 8: Add assistant response to context
        self.context.add_assistant_message(response)
        
        # Step 9: Prepare metadata
        metadata = {
            "emotion": emotion,
            "intensity": intensity,
            "scenario": scenario,
            "is_policy_question": is_policy_q,
            "rag_used": rag_result is not None,
            "rag_confidence": rag_result.get("confidence") if rag_result else None,
            "message_count": len(self.context),
            "token_usage": self.context.get_context_window_usage()
        }
        
        # Update statistics
        self.total_messages_processed += 1
        
        return response, metadata
    
    def _determine_scenario(self, emotion: str, facts: Optional[Dict], is_policy_q: bool) -> str:
        """
        Determine the appropriate scenario based on emotion and context
        
        Args:
            emotion: Detected emotion
            facts: Available facts
            is_policy_q: Whether this is a policy question
        
        Returns:
            Scenario identifier
        """
        # Policy questions get their own scenario
        if is_policy_q:
            return "policy_question"
        
        # If frustrated, use frustrated customer scenario
        if emotion == "frustrated":
            return "frustrated_customer"
        
        # If has order info and is about delay
        if facts and facts.get("status") == "delayed":
            return "delay_explanation"
        
        # If has order info (standard query)
        if facts and "order_id" in facts:
            return "order_status_simple"
        
        # Default to general query
        return "general_query"
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of current conversation state"""
        summary = {
            "messages": len(self.context),
            "emotions_detected": self.emotions_detected,
            "total_processed": self.total_messages_processed,
            "context_summary": self.context.get_conversation_summary()
        }
        
        # Add RAG stats if available
        if self.rag_available:
            summary["rag_stats"] = self.rag_stats
        
        return summary
    
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
        # Reset RAG stats
        self.rag_stats = {
            "policy_questions": 0,
            "rag_retrievals": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "escalations": 0
        }
    
    def get_context(self) -> ConversationContext:
        """Get the conversation context"""
        return self.context
    
    def __repr__(self) -> str:
        """String representation"""
        rag_status = "RAG enabled" if self.rag_available else "RAG disabled"
        return f"ConversationOrchestrator(messages={len(self.context)}, processed={self.total_messages_processed}, {rag_status})"


# Factory function
def create_orchestrator(
    brand_name: str = "fashionhub",
    brand_voice: Optional[Dict] = None,
    system_prompt: str = "You are a helpful customer support agent."
) -> ConversationOrchestrator:
    """
    Create a new conversation orchestrator
    
    Args:
        brand_name: Brand name for RAG
        brand_voice: Brand voice guidelines
        system_prompt: System prompt
    
    Returns:
        New ConversationOrchestrator instance
    """
    return ConversationOrchestrator(
        brand_name=brand_name,
        brand_voice=brand_voice,
        system_prompt=system_prompt
    )
