"""
Conversation Orchestrator - BRAND-AWARE
Coordinates: Memory + Emotion + RAG + Tools + BRAND VOICE
"""

from typing import Dict, Tuple, Optional
from core.conversation.context import ConversationContext
from core.emotion.detector import EmotionDetector
from core.llm.composer import LLMResponseComposer
from core.rag.retriever import KnowledgeRetriever
from core.tools.registry import ToolRegistry
from core.brands.prompt_builder import build_system_prompt
from core.brands.registry import get_brand_registry
import re


class ConversationOrchestrator:
    """Orchestrates conversation with BRAND-SPECIFIC VOICE"""
    
    def __init__(
        self,
        brand_id: str = "fashionhub",  # Now required!
        brand_voice: Optional[Dict] = None,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize orchestrator with brand
        
        Args:
            brand_id: Brand identifier (REQUIRED)
            brand_voice: Legacy parameter (now loaded from config)
            system_prompt: Override system prompt (optional)
        """
        # Validate brand exists
        registry = get_brand_registry()
        if not registry.validate_brand_id(brand_id):
            raise ValueError(f"Invalid brand_id: {brand_id}")
        
        self.brand_id = brand_id
        self.brand_config = registry.get_brand_by_id(brand_id)
        
        # Core components
        self.context = ConversationContext()
        self.composer = LLMResponseComposer()
        
        # Build brand-specific system prompt
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            self.system_prompt = build_system_prompt(brand_id)
            print(f"✅ Loaded brand voice for: {self.brand_config['name']}")
        
        # RAG (brand-scoped)
        try:
            self.retriever = KnowledgeRetriever(brand_id)
            self.rag_available = True
            print(f"✅ RAG enabled for {brand_id}")
        except Exception as e:
            print(f"⚠️  RAG not available: {e}")
            self.retriever = None
            self.rag_available = False
        
        # Tools (brand-scoped)
        try:
            self.tools = ToolRegistry(brand_id)
            self.tools_available = True
            print(f"✅ Tools enabled: {self.tools.list_tools()}")
        except Exception as e:
            print(f"⚠️  Tools not available: {e}")
            self.tools = None
            self.tools_available = False
        
        # Statistics
        self.total_messages_processed = 0
        self.emotions_detected = {
            "frustrated": 0, "confused": 0, "urgent": 0, 
            "positive": 0, "neutral": 0
        }
        self.rag_stats = {
            "policy_questions": 0, "rag_retrievals": 0,
            "high_confidence": 0, "medium_confidence": 0,
            "low_confidence": 0, "escalations": 0
        }
        self.tool_stats = {
            "tool_calls": 0, "tool_successes": 0, "tool_failures": 0,
            "order_queries": 0, "knowledge_queries": 0
        }
    
    def process_message(
        self,
        user_message: str,
        facts: Optional[Dict] = None,
        constraints: Optional[list] = None
    ) -> Tuple[str, Dict]:
        """Process message with brand-specific voice"""
        
        # Add to context
        self.context.add_user_message(user_message)
        
        # Detect emotion
        emotion, intensity, triggers = EmotionDetector.detect_emotion(user_message)
        self.context.update_metadata("last_emotion", emotion)
        
        if emotion in self.emotions_detected:
            self.emotions_detected[emotion] += 1
        
        if facts is None:
            facts = {}
        
        # Add brand context to facts
        facts["brand_name"] = self.brand_config.get("name")
        facts["brand_voice"] = self.brand_config.get("voice", {})
        
        # Tool execution
        tool_used = None
        tool_result = None
        tool_success = False
        
        if self.tools_available:
            selected_tool = self.tools.select_tool(user_message)
            
            if selected_tool:
                print(f"🔧 Selected tool: {selected_tool}")
                self.tool_stats["tool_calls"] += 1
                
                tool_params = self._extract_tool_params(user_message, selected_tool)
                
                if tool_params:
                    tool_result = self.tools.execute_tool(selected_tool, **tool_params)
                    tool_used = selected_tool
                    
                    if tool_result["success"]:
                        self.tool_stats["tool_successes"] += 1
                        tool_success = True
                        
                        if selected_tool == "get_order_status":
                            facts["order_data"] = tool_result["data"]
                            self.tool_stats["order_queries"] += 1
                        elif selected_tool == "search_knowledge":
                            facts["knowledge_data"] = tool_result["data"]
                            self.tool_stats["knowledge_queries"] += 1
                        elif selected_tool == "check_shipping_eligibility":
                            facts["shipping_data"] = tool_result["data"]
                        elif selected_tool == "get_product_info":
                            facts["product_data"] = tool_result["data"]
                    else:
                        self.tool_stats["tool_failures"] += 1
                        facts["tool_error"] = tool_result["error"]
        
        # Determine scenario
        scenario = self._determine_scenario(emotion, facts, tool_used)
        
        # Generate response with brand-specific system prompt
        response = self.composer.compose_response(
            scenario=scenario,
            facts=facts,
            constraints=constraints or [],
            emotion=emotion,
            brand_voice=self.brand_config.get("voice", {}),
            system_prompt=self.system_prompt  # Brand-specific!
        )
        
        # Add to context
        self.context.add_assistant_message(response)
        
        # Metadata
        metadata = {
            "brand_id": self.brand_id,
            "brand_name": self.brand_config.get("name"),
            "emotion": emotion,
            "intensity": intensity,
            "scenario": scenario,
            "tool_used": tool_used,
            "tool_success": tool_success,
            "rag_used": False,
            "rag_confidence": None,
            "message_count": len(self.context),
            "token_usage": self.context.get_context_window_usage()
        }
        
        self.total_messages_processed += 1
        
        return response, metadata
    
    def _extract_tool_params(self, message: str, tool_name: str) -> Dict:
        """Extract parameters for tool"""
        params = {}
        
        if tool_name == "get_order_status":
            match = re.search(r'\b(\d{4,5})\b', message)
            if match:
                params["order_id"] = match.group(1)
        
        elif tool_name == "check_shipping_eligibility":
            match = re.search(r'\b(\d{6})\b', message)
            if match:
                params["pincode"] = match.group(1)
        
        elif tool_name == "search_knowledge":
            params["query"] = message
        
        return params
    
    def _determine_scenario(self, emotion: str, facts: Dict, tool_used: str) -> str:
        """Determine response scenario"""
        if tool_used == "get_order_status" and facts.get("order_data"):
            if emotion == "frustrated":
                return "frustrated_customer_with_order"
            return "order_status_query"
        
        if tool_used == "search_knowledge" and facts.get("knowledge_data"):
            return "policy_question"
        
        if tool_used == "check_shipping_eligibility" and facts.get("shipping_data"):
            return "shipping_inquiry"
        
        if emotion == "frustrated":
            return "frustrated_customer"
        
        return "general_query"
    
    def get_conversation_summary(self) -> Dict:
        """Get conversation summary"""
        return {
            "brand_id": self.brand_id,
            "brand_name": self.brand_config.get("name"),
            "messages": len(self.context),
            "emotions_detected": self.emotions_detected,
            "total_processed": self.total_messages_processed,
            "tool_stats": self.tool_stats,
            "rag_stats": self.rag_stats,
            "context_summary": self.context.get_conversation_summary()
        }
    
    def clear_conversation(self):
        """Clear everything"""
        self.context.clear()
        self.total_messages_processed = 0
        self.emotions_detected = {k: 0 for k in self.emotions_detected}
        self.rag_stats = {k: 0 for k in self.rag_stats}
        self.tool_stats = {k: 0 for k in self.tool_stats}
    
    def __repr__(self) -> str:
        return f"ConversationOrchestrator(brand={self.brand_id}, messages={len(self.context)})"
