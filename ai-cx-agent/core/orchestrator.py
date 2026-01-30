"""
Conversation Orchestrator
Coordinates: Memory + Emotion + RAG + TOOLS
NOW WITH TOOL INTEGRATION!
"""

from typing import Dict, Tuple, Optional
from core.conversation.context import ConversationContext
from core.emotion.detector import EmotionDetector
from core.llm.composer import LLMResponseComposer
from core.rag.retriever import KnowledgeRetriever
from core.tools.registry import ToolRegistry
import re


class ConversationOrchestrator:
    """
    Orchestrates conversation with full tool integration
    """
    
    def __init__(
        self,
        brand_name: str = "fashionhub",
        brand_voice: Optional[Dict] = None,
        system_prompt: str = "You are a helpful customer support agent."
    ):
        """Initialize orchestrator with all components"""
        # Core components
        self.context = ConversationContext()
        self.composer = LLMResponseComposer()
        
        # RAG
        self.brand_name = brand_name
        try:
            self.retriever = KnowledgeRetriever(brand_name)
            self.rag_available = True
        except Exception as e:
            print(f"⚠️  RAG not available: {e}")
            self.retriever = None
            self.rag_available = False
        
        # TOOLS (NEW!)
        try:
            self.tools = ToolRegistry(brand_name)
            self.tools_available = True
            print(f"✅ Tools enabled: {self.tools.list_tools()}")
        except Exception as e:
            print(f"⚠️  Tools not available: {e}")
            self.tools = None
            self.tools_available = False
        
        # Configuration
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
        
        # RAG stats
        self.rag_stats = {
            "policy_questions": 0,
            "rag_retrievals": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "escalations": 0
        }
        
        # TOOL stats (NEW!)
        self.tool_stats = {
            "tool_calls": 0,
            "tool_successes": 0,
            "tool_failures": 0,
            "order_queries": 0,
            "knowledge_queries": 0
        }
    
    def _extract_order_id(self, message: str) -> Optional[str]:
        """Extract order ID from message"""
        # Look for 4-5 digit numbers
        match = re.search(r'\b(\d{4,5})\b', message)
        return match.group(1) if match else None
    
    def _is_policy_question(self, message: str) -> bool:
        """Detect if message is a policy question"""
        policy_keywords = [
            "policy", "return", "refund", "exchange", "shipping",
            "delivery", "cancel", "cancellation", "free shipping",
            "how long", "how do i", "can i return", "can i cancel",
            "what if", "do you offer", "is there"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in policy_keywords)
    
    def _retrieve_knowledge(self, query: str) -> Optional[Dict]:
        """Retrieve from RAG"""
        if not self.rag_available:
            return None
        
        try:
            self.rag_stats["rag_retrievals"] += 1
            result = self.retriever.retrieve_with_confidence(query)
            
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
            print(f"⚠️  RAG error: {e}")
            return None
    
    def _format_rag_context(self, rag_result: Dict) -> str:
        """Format RAG results for LLM"""
        if not rag_result or not rag_result.get("found"):
            return ""
        
        context = "RELEVANT POLICY INFORMATION:\n\n"
        for i, result in enumerate(rag_result["results"][:3], 1):
            context += f"[Source {i}: {result['source']}]\n"
            context += f"{result['text']}\n\n"
        
        return context
    
    def process_message(
        self,
        user_message: str,
        facts: Optional[Dict] = None,
        constraints: Optional[list] = None
    ) -> Tuple[str, Dict]:
        """
        Process message with FULL TOOL INTEGRATION
        
        Args:
            user_message: User's message
            facts: Additional facts
            constraints: Constraints
        
        Returns:
            (response, metadata)
        """
        # Step 1: Add to context
        self.context.add_user_message(user_message)
        
        # Step 2: Detect emotion
        emotion, intensity, triggers = EmotionDetector.detect_emotion(user_message)
        self.context.update_metadata("last_emotion", emotion)
        
        if emotion in self.emotions_detected:
            self.emotions_detected[emotion] += 1
        
        # Initialize facts
        if facts is None:
            facts = {}
        
        # Step 3: CHECK FOR ORDER QUERY (TOOL!)
        order_id = self._extract_order_id(user_message)
        tool_used = None
        tool_result = None
        
        if order_id and self.tools_available:
            print(f"🔧 Order ID detected: {order_id}, using order tool...")
            self.tool_stats["tool_calls"] += 1
            self.tool_stats["order_queries"] += 1
            
            # Use order tool
            tool_result = self.tools.execute_tool("get_order_status", order_id=order_id)
            tool_used = "get_order_status"
            
            if tool_result["success"]:
                self.tool_stats["tool_successes"] += 1
                # Add order data to facts
                facts["order_data"] = tool_result["data"]
                print(f"   ✅ Order found: {tool_result['data']['customer_name']}")
            else:
                self.tool_stats["tool_failures"] += 1
                facts["order_error"] = tool_result["error"]
                print(f"   ❌ Order tool failed: {tool_result['error']}")
        
        # Step 4: CHECK FOR POLICY QUESTION (RAG!)
        is_policy_q = self._is_policy_question(user_message)
        rag_result = None
        rag_context = ""
        
        if is_policy_q and self.rag_available and not order_id:
            self.rag_stats["policy_questions"] += 1
            print(f"🔍 Policy question detected, retrieving from knowledge base...")
            
            rag_result = self._retrieve_knowledge(user_message)
            
            if rag_result and rag_result.get("found"):
                rag_context = self._format_rag_context(rag_result)
                print(f"   ✅ Retrieved with {rag_result['confidence']} confidence")
                facts["knowledge_context"] = rag_context
        
        # Step 5: Determine scenario
        scenario = self._determine_scenario(emotion, facts, is_policy_q, order_id is not None)
        
        # Step 6: Generate response
        response = self.composer.compose_response(
            scenario=scenario,
            facts=facts,
            constraints=constraints or [],
            emotion=emotion,
            brand_voice=self.brand_voice
        )
        
        # Step 7: Add to context
        self.context.add_assistant_message(response)
        
        # Step 8: Metadata
        metadata = {
            "emotion": emotion,
            "intensity": intensity,
            "scenario": scenario,
            "is_policy_question": is_policy_q,
            "order_id": order_id,
            "tool_used": tool_used,
            "tool_success": tool_result["success"] if tool_result else None,
            "rag_used": rag_result is not None,
            "rag_confidence": rag_result.get("confidence") if rag_result else None,
            "message_count": len(self.context),
            "token_usage": self.context.get_context_window_usage()
        }
        
        self.total_messages_processed += 1
        
        return response, metadata
    
    def _determine_scenario(self, emotion: str, facts: Dict, is_policy_q: bool, has_order: bool) -> str:
        """Determine scenario"""
        if has_order and facts.get("order_data"):
            if emotion == "frustrated":
                return "frustrated_customer_with_order"
            return "order_status_query"
        
        if is_policy_q:
            return "policy_question"
        
        if emotion == "frustrated":
            return "frustrated_customer"
        
        return "general_query"
    
    def get_conversation_summary(self) -> Dict:
        """Get conversation summary with tool stats"""
        summary = {
            "messages": len(self.context),
            "emotions_detected": self.emotions_detected,
            "total_processed": self.total_messages_processed,
            "context_summary": self.context.get_conversation_summary()
        }
        
        if self.rag_available:
            summary["rag_stats"] = self.rag_stats
        
        if self.tools_available:
            summary["tool_stats"] = self.tool_stats
        
        return summary
    
    def clear_conversation(self):
        """Clear everything"""
        self.context.clear()
        self.total_messages_processed = 0
        self.emotions_detected = {k: 0 for k in self.emotions_detected}
        self.rag_stats = {k: 0 for k in self.rag_stats}
        self.tool_stats = {k: 0 for k in self.tool_stats}
    
    def __repr__(self) -> str:
        status = []
        if self.rag_available:
            status.append("RAG")
        if self.tools_available:
            status.append("Tools")
        
        return f"ConversationOrchestrator(messages={len(self.context)}, {', '.join(status)})"
