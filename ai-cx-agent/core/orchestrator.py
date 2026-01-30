"""
Conversation Orchestrator
Coordinates: Memory + Emotion + RAG + TOOLS
FIXED: Now actually calls tools!
"""

from typing import Dict, Tuple, Optional
from core.conversation.context import ConversationContext
from core.emotion.detector import EmotionDetector
from core.llm.composer import LLMResponseComposer
from core.rag.retriever import KnowledgeRetriever
from core.tools.registry import ToolRegistry
import re


class ConversationOrchestrator:
    """Orchestrates conversation with full tool integration"""
    
    def __init__(
        self,
        brand_name: str = "fashionhub",
        brand_voice: Optional[Dict] = None,
        system_prompt: str = "You are a helpful customer support agent."
    ):
        """Initialize orchestrator"""
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
        
        # TOOLS
        try:
            self.tools = ToolRegistry(brand_name)
            self.tools_available = True
            print(f"✅ Tools enabled: {self.tools.list_tools()}")
        except Exception as e:
            print(f"⚠️  Tools not available: {e}")
            self.tools = None
            self.tools_available = False
        
        self.brand_voice = brand_voice or {}
        self.system_prompt = system_prompt
        
        # Statistics
        self.total_messages_processed = 0
        self.emotions_detected = {"frustrated": 0, "confused": 0, "urgent": 0, "positive": 0, "neutral": 0}
        self.rag_stats = {"policy_questions": 0, "rag_retrievals": 0, "high_confidence": 0, "medium_confidence": 0, "low_confidence": 0, "escalations": 0}
        self.tool_stats = {"tool_calls": 0, "tool_successes": 0, "tool_failures": 0, "order_queries": 0, "knowledge_queries": 0}
    
    def process_message(
        self,
        user_message: str,
        facts: Optional[Dict] = None,
        constraints: Optional[list] = None
    ) -> Tuple[str, Dict]:
        """Process message with FULL TOOL INTEGRATION"""
        
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
        
        # Step 3: SELECT AND EXECUTE TOOL
        tool_used = None
        tool_result = None
        tool_success = False
        
        if self.tools_available:
            # Let tool registry select the right tool
            selected_tool = self.tools.select_tool(user_message)
            
            if selected_tool:
                print(f"🔧 Selected tool: {selected_tool}")
                self.tool_stats["tool_calls"] += 1
                
                # Extract parameters
                tool_params = self._extract_tool_params(user_message, selected_tool)
                
                if tool_params:
                    # Execute tool
                    tool_result = self.tools.execute_tool(selected_tool, **tool_params)
                    tool_used = selected_tool
                    
                    if tool_result["success"]:
                        self.tool_stats["tool_successes"] += 1
                        tool_success = True
                        
                        # Add tool data to facts
                        if selected_tool == "get_order_status":
                            facts["order_data"] = tool_result["data"]
                            self.tool_stats["order_queries"] += 1
                            print(f"   ✅ Order data retrieved")
                        
                        elif selected_tool == "search_knowledge":
                            facts["knowledge_data"] = tool_result["data"]
                            self.tool_stats["knowledge_queries"] += 1
                            print(f"   ✅ Knowledge retrieved")
                        
                        elif selected_tool == "check_shipping_eligibility":
                            facts["shipping_data"] = tool_result["data"]
                            print(f"   ✅ Shipping data retrieved")
                        
                        elif selected_tool == "get_product_info":
                            facts["product_data"] = tool_result["data"]
                            print(f"   ✅ Product data retrieved")
                    else:
                        self.tool_stats["tool_failures"] += 1
                        facts["tool_error"] = tool_result["error"]
                        print(f"   ❌ Tool failed: {tool_result['error']}")
                else:
                    print(f"   ⚠️  Could not extract parameters for {selected_tool}")
        
        # Step 4: Determine scenario
        scenario = self._determine_scenario(emotion, facts, tool_used)
        
        # Step 5: Generate response
        response = self.composer.compose_response(
            scenario=scenario,
            facts=facts,
            constraints=constraints or [],
            emotion=emotion,
            brand_voice=self.brand_voice
        )
        
        # Step 6: Add to context
        self.context.add_assistant_message(response)
        
        # Step 7: Metadata
        metadata = {
            "emotion": emotion,
            "intensity": intensity,
            "scenario": scenario,
            "tool_used": tool_used,
            "tool_success": tool_success,
            "rag_used": False,  # Tool system handles knowledge now
            "rag_confidence": None,
            "message_count": len(self.context),
            "token_usage": self.context.get_context_window_usage()
        }
        
        self.total_messages_processed += 1
        
        return response, metadata
    
    def _extract_tool_params(self, message: str, tool_name: str) -> Dict:
        """Extract parameters for tool from message"""
        params = {}
        
        if tool_name == "get_order_status":
            match = re.search(r'\b(\d{4,5})\b', message)
            if match:
                params["order_id"] = match.group(1)
        
        elif tool_name == "check_shipping_eligibility":
            match = re.search(r'\b(\d{6})\b', message)
            if match:
                params["pincode"] = match.group(1)
                # Try to extract order value if mentioned
                value_match = re.search(r'₹\s*(\d+)', message)
                if value_match:
                    params["order_value"] = float(value_match.group(1))
        
        elif tool_name == "search_knowledge":
            params["query"] = message
        
        elif tool_name == "get_product_info":
            # Would need product ID - for now skip
            pass
        
        return params
    
    def _determine_scenario(self, emotion: str, facts: Dict, tool_used: str) -> str:
        """Determine scenario"""
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
