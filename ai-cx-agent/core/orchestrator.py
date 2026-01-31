"""
Conversation Orchestrator - WITH ESCALATION MANAGEMENT
Coordinates: Memory + Emotion + RAG + Tools + Brand Voice + Context + Escalation
"""

from typing import Dict, Tuple, Optional
from datetime import datetime
from core.conversation.context import ConversationContext
from core.emotion.detector import EmotionDetector
from core.llm.composer import LLMResponseComposer
from core.rag.retriever import KnowledgeRetriever
from core.tools.registry import ToolRegistry
from core.brands.prompt_builder import build_system_prompt
from core.brands.registry import get_brand_registry
from core.conversation.context_resolver import ContextResolver
from core.conversation.escalation_manager import EscalationManager
import re


class ConversationOrchestrator:
    """Orchestrates conversation with context resolution AND escalation management"""
    
    def __init__(
        self,
        brand_id: str = "fashionhub",
        brand_voice: Optional[Dict] = None,
        system_prompt: Optional[str] = None
    ):
        """Initialize orchestrator"""
        
        # Validate brand
        registry = get_brand_registry()
        if not registry.validate_brand_id(brand_id):
            raise ValueError(f"Invalid brand_id: {brand_id}")
        
        self.brand_id = brand_id
        self.brand_config = registry.get_brand_by_id(brand_id)
        
        # Core components
        self.context = ConversationContext()
        self.composer = LLMResponseComposer()
        
        # Intelligence components
        self.context_resolver = ContextResolver(self.composer.client)
        self.escalation_manager = EscalationManager()
        
        self.active_topic = None
        self.emotion_history = []
        
        # Build brand-specific system prompt
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            self.system_prompt = build_system_prompt(brand_id)
            print(f"✅ Loaded brand voice for: {self.brand_config['name']}")
        
        # RAG
        try:
            self.retriever = KnowledgeRetriever(brand_id)
            self.rag_available = True
            print(f"✅ RAG enabled for {brand_id}")
        except Exception as e:
            self.retriever = None
            self.rag_available = False
        
        # Tools
        try:
            self.tools = ToolRegistry(brand_id)
            self.tools_available = True
            print(f"✅ Tools enabled: {self.tools.list_tools()}")
        except Exception as e:
            self.tools = None
            self.tools_available = False
        
        # Statistics
        self.total_messages_processed = 0
        self.emotions_detected = {
            "frustrated": 0, "confused": 0, "urgent": 0,
            "positive": 0, "neutral": 0
        }
        self.tool_stats = {
            "tool_calls": 0, "tool_successes": 0, "tool_failures": 0,
            "order_queries": 0, "knowledge_queries": 0
        }
        self.context_stats = {
            "context_resolutions": 0,
            "context_maintained": 0,
            "topic_switches": 0
        }
        self.escalation_stats = {
            "escalations_triggered": 0,
            "escalations_prevented": 0,
            "tier1_escalations": 0,
            "tier2_escalations": 0
        }
    
    def process_message(
        self,
        user_message: str,
        facts: Optional[Dict] = None,
        constraints: Optional[list] = None
    ) -> Tuple[str, Dict]:
        """Process message with context resolution AND escalation management"""
        
        # Add to context
        self.context.add_user_message(user_message)
        
        # Detect emotion
        emotion, intensity, triggers = EmotionDetector.detect_emotion(user_message)
        self.context.update_metadata("last_emotion", emotion)
        
        if emotion in self.emotions_detected:
            self.emotions_detected[emotion] += 1
        
        # Track emotion history
        self.emotion_history.append({
            'emotion': emotion,
            'intensity': intensity,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 10 emotions
        if len(self.emotion_history) > 10:
            self.emotion_history = self.emotion_history[-10:]
        
        if facts is None:
            facts = {}
        
        # Add brand context
        facts["brand_name"] = self.brand_config.get("name")
        facts["brand_voice"] = self.brand_config.get("voice", {})
        
        # === ESCALATION CHECK ===
        escalation_check = self.escalation_manager.should_escalate({
            'message': user_message,
            'emotion': emotion,
            'emotion_history': self.emotion_history,
            'confidence': 1.0,
            'scenario': '',
            'tool_failures': self.tool_stats.get('tool_failures', 0)
        })
        
        if escalation_check['should_escalate']:
            print(f"🚨 ESCALATION: Tier {escalation_check['escalation_tier']} - {escalation_check['reason']}")
            
            self.escalation_stats["escalations_triggered"] += 1
            
            if escalation_check['escalation_tier'] == 1:
                self.escalation_stats["tier1_escalations"] += 1
            elif escalation_check['escalation_tier'] == 2:
                self.escalation_stats["tier2_escalations"] += 1
            
            facts['escalation'] = escalation_check
            self.escalation_manager.log_escalation(escalation_check)
        
        elif escalation_check.get('prevent_escalation'):
            print(f"💚 Escalation prevented: Empathy first")
            self.escalation_stats["escalations_prevented"] += 1
            facts['empathy_needed'] = True
        
        # === CONTEXT RESOLUTION ===
        if self.active_topic:
            context_result = self.context_resolver.resolve_context(
                user_message,
                self.active_topic
            )
            
            self.context_stats["context_resolutions"] += 1
            
            if context_result['about_current_topic'] and context_result['confidence'] > 0.7:
                print(f"💡 Context resolved: '{user_message}' → {self.active_topic['topic_type']} {self.active_topic['entity_id']}")
                
                facts['active_topic'] = self.active_topic
                facts['context_confidence'] = context_result['confidence']
                self.context_stats["context_maintained"] += 1
            else:
                print(f"🔄 New topic detected")
                self.active_topic = None
                self.context_stats["topic_switches"] += 1
        
        # Tool execution
        tool_used = None
        tool_result = None
        tool_success = False
        
        if self.tools_available and not facts.get('escalation'):  # Skip tools if escalating
            selected_tool = self.tools.select_tool(user_message)
            
            if selected_tool:
                print(f"🔧 Selected tool: {selected_tool}")
                self.tool_stats["tool_calls"] += 1
                
                tool_params = self._extract_tool_params(user_message, selected_tool)
                
                if tool_params:
                    # Set topic when tool selected
                    if selected_tool == "get_order_status" and tool_params.get('order_id'):
                        self.active_topic = {
                            'topic_type': 'ORDER',
                            'entity_id': tool_params.get('order_id'),
                            'context': 'User asked about order status'
                        }
                        print(f"📌 Active topic set: ORDER {tool_params.get('order_id')}")
                    
                    elif selected_tool == "search_knowledge":
                        self.active_topic = {
                            'topic_type': 'POLICY',
                            'entity_id': 'general',
                            'context': user_message
                        }
                        print(f"📌 Active topic set: POLICY")
                    
                    # Execute tool
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
        if facts.get('escalation'):
            scenario = 'escalation_needed'
        else:
            scenario = self._determine_scenario(emotion, facts, tool_used)
        
        # Generate response
        response = self.composer.compose_response(
            scenario=scenario,
            facts=facts,
            constraints=constraints or [],
            emotion=emotion,
            brand_voice=self.brand_config.get("voice", {}),
            system_prompt=self.system_prompt
        )
        
        # If escalation suggested message exists, use it
        if facts.get('escalation') and facts['escalation'].get('suggested_message'):
            response = facts['escalation']['suggested_message']
        
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
            "active_topic": self.active_topic,
            "context_maintained": bool(self.active_topic and facts.get('context_confidence')),
            "escalation": facts.get('escalation'),
            "message_count": len(self.context),
            "token_usage": self.context.get_context_window_usage()
        }
        
        self.total_messages_processed += 1
        
        return response, metadata
    
    def _extract_tool_params(self, message: str, tool_name: str) -> Dict:
        """Extract parameters for tool"""
        params = {}
        
        # If we have active topic and message is about it, use topic context
        if self.active_topic and self.active_topic.get('entity_id'):
            if tool_name == "get_order_status" and self.active_topic['topic_type'] == 'ORDER':
                params["order_id"] = self.active_topic['entity_id']
                print(f"   Using context: order_id={self.active_topic['entity_id']}")
                return params
        
        # Otherwise, extract from message
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
            "context_stats": self.context_stats,
            "escalation_stats": self.escalation_stats,
            "active_topic": self.active_topic,
            "context_summary": self.context.get_conversation_summary()
        }
    
    def clear_conversation(self):
        """Clear everything"""
        self.context.clear()
        self.active_topic = None
        self.emotion_history = []
        self.total_messages_processed = 0
        self.emotions_detected = {k: 0 for k in self.emotions_detected}
        self.tool_stats = {k: 0 for k in self.tool_stats}
        self.context_stats = {k: 0 for k in self.context_stats}
        self.escalation_stats = {k: 0 for k in self.escalation_stats}
    
    def __repr__(self) -> str:
        topic_info = f", topic={self.active_topic['topic_type']}" if self.active_topic else ""
        return f"ConversationOrchestrator(brand={self.brand_id}, messages={len(self.context)}{topic_info})"
