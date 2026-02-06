"""
Conversation Orchestrator - WITH QUALITY MONITORING
Coordinates: Memory + Emotion + RAG + Tools + Brand Voice + Context + Escalation + Quality
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
from core.conversation.quality_scorer import ConversationQualityScorer
from core.intelligence.intent_classifier import IntentClassifier
from core.llm.response_composer import ResponseComposer
from core.conversation.smart_escalation import SmartEscalationManager
import re
from core.intelligence.analyzer import IntelligenceAnalyzer


class ConversationOrchestrator:
    """Orchestrates conversation with full intelligence stack + quality monitoring"""
    
    def __init__(
        self,
        brand_id: str = "fashionhub",
        brand_voice: Optional[Dict] = None,
        system_prompt: Optional[str] = None
    ):
        """Initialize orchestrator with all intelligence components"""
        
        # Validate brand
        registry = get_brand_registry()
        if not registry.validate_brand_id(brand_id):
            raise ValueError(f"Invalid brand_id: {brand_id}")
        
        self.brand_id = brand_id
        self.brand_config = registry.get_brand_by_id(brand_id)
        
        # Core components
        self.context = ConversationContext()
        self.composer = LLMResponseComposer()
        
        # Intelligence components - NEW
        self.intent_classifier = IntentClassifier()
        self.response_composer = ResponseComposer()
        self.smart_escalation_manager = SmartEscalationManager()
        
        # OLD intelligence components (keep for backwards compatibility)
        self.context_resolver = ContextResolver(self.composer.client)
        self.escalation_manager = EscalationManager()
        self.quality_scorer = ConversationQualityScorer()
        
        self.active_topic = None
        self.emotion_history = []
        self.quality_history = []
        
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
        self.quality_stats = {
            "avg_overall": 0.0,
            "avg_context": 0.0,
            "avg_empathy": 0.0,
            "avg_accuracy": 0.0,
            "avg_efficiency": 0.0,
            "avg_brand_voice": 0.0
        }
    
    def process_message(
        self,
        user_message: str,
        facts: Optional[Dict] = None,
        constraints: Optional[list] = None
    ) -> Tuple[str, Dict]:
        """Process message with full intelligence + quality scoring"""
        
        # ========== NEW INTELLIGENCE LAYER ==========
        
        # === STEP 1: ANALYZE INTENT ===
        intent = self.intent_classifier.analyze(
            user_message=user_message,
            context={'order_number': self.active_topic.get('entity_id') if self.active_topic else None}
        )
        
        print(f"🧠 Intent: {intent.primary_intent}")
        print(f"❓ Specific: {intent.specific_question}")
        print(f"😊 Emotion: {intent.user_emotion}")
        
        # === STEP 2: HANDLE MISSING DATA ===
        if intent.missing_data:
            response = self.response_composer._compose_missing_data_response(intent)
            metadata = {
                'intent': intent.primary_intent,
                'missing_data': intent.missing_data,
                'handled_by': 'response_composer'
            }
            return response, metadata
        
        # ========== EXISTING CODE CONTINUES ==========
        
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
        
        if len(self.emotion_history) > 10:
            self.emotion_history = self.emotion_history[-10:]
        
        if facts is None:
            facts = {}
        
        # Add brand context
        facts["brand_name"] = self.brand_config.get("name")
        facts["brand_voice"] = self.brand_config.get("voice", {})
        
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
        
        # ========== NEW: GATHER TOOL RESULTS FOR COMPOSER ==========
        
        tool_results_for_composer = {}
        
        if intent.primary_intent in [
            'order_status_inquiry', 
            'order_contents_inquiry',
            'cancel_order', 
            'refund_request',
            'exchange_request',
            'change_address',
            'problem_report'
        ]:
            # Need order data
            order_id = None
            
            # Try to get from active topic
            if self.active_topic and self.active_topic.get('topic_type') == 'ORDER':
                order_id = self.active_topic.get('entity_id')
            
            # Or extract from message
            if not order_id:
                match = re.search(r'\b(\d{4,5})\b', user_message)
                if match:
                    order_id = match.group(1)
            
            # Get order data
            if order_id and self.tools_available:
                from core.tools.order_tool import get_order_status
                order_data = get_order_status(order_id, self.brand_id)
                if order_data.get('success'):
                    tool_results_for_composer['order_data'] = order_data.get('data', {})
                    print(f"📦 Loaded order data for composer: {order_id}")
        
        # ========== EXISTING TOOL EXECUTION CODE ==========
        
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
        scenario = self._determine_scenario(emotion, facts, tool_used)
        
        # === INTELLIGENCE ANALYSIS ===
        if facts.get("order_data"):
            analysis = IntelligenceAnalyzer.analyze_question_intent(user_message, facts["order_data"])
            
            if analysis.get('special_instructions'):
                facts['intelligence_analysis'] = analysis
                print(f"🧠 Intelligence: {analysis['question_type']}")
        elif facts.get("active_topic") and facts["active_topic"].get('topic_type') == 'ORDER':
            order_id = facts["active_topic"].get('entity_id')
            if order_id:
                from core.tools.order_tool import get_order_status
                order_data = get_order_status(order_id, self.brand_id)
                if order_data.get('success'):
                    facts['order_data'] = order_data
                    analysis = IntelligenceAnalyzer.analyze_question_intent(user_message, order_data)
                    if analysis.get('special_instructions'):
                        facts['intelligence_analysis'] = analysis
                        print(f"🧠 Intelligence: {analysis['question_type']} (from context)")
        
        # ========== NEW: USE SMART ESCALATION & RESPONSE COMPOSER ==========
        
        # Check if we should escalate using NEW smart escalation
        should_escalate, escalation_reason = self.smart_escalation_manager.should_escalate(
            intent,
            tool_results_for_composer,
            self.emotion_history
        )
        
        if should_escalate:
            print(f"🚨 SMART ESCALATION: {escalation_reason}")
            response = self.smart_escalation_manager.get_escalation_message(intent, escalation_reason)
            
            # Track escalation
            self.escalation_stats["escalations_triggered"] += 1
            
        else:
            # === USE NEW RESPONSE COMPOSER ===
            print(f"✨ Using smart response composer")
            response = self.response_composer.compose(
                user_message=user_message,
                intent=intent,
                tool_results=tool_results_for_composer,
                context={'order_number': self.active_topic.get('entity_id') if self.active_topic else None}
            )
        
        # Add to context
        self.context.add_assistant_message(response)
        
        # === QUALITY SCORING ===
        quality_score = self.quality_scorer.score_exchange({
            'user_message': user_message,
            'agent_response': response,
            'emotion': emotion,
            'scenario': scenario,
            'context_used': bool(self.active_topic and facts.get('context_confidence')),
            'tool_results': tool_result or {},
            'metadata': {
                'tool_used': tool_used,
                'tool_success': tool_success,
                'active_topic': self.active_topic,
                'escalation': should_escalate
            },
            'brand_config': self.brand_config
        })
        
        self.quality_history.append(quality_score)
        
        # Update quality stats
        avg_scores = self.quality_scorer.get_average_scores()
        self.quality_stats = {
            'avg_overall': avg_scores['overall'],
            'avg_context': avg_scores['context_retention'],
            'avg_empathy': avg_scores['empathy'],
            'avg_accuracy': avg_scores['accuracy'],
            'avg_efficiency': avg_scores['efficiency'],
            'avg_brand_voice': avg_scores['brand_voice']
        }
        
        # Show quality score
        if quality_score['overall'] >= 8.0:
            print(f"⭐ Quality: {quality_score['overall']}/10 ({quality_score['grade']}) - Excellent!")
        elif quality_score['overall'] >= 7.0:
            print(f"✓ Quality: {quality_score['overall']}/10 ({quality_score['grade']}) - Good")
        else:
            print(f"⚠️  Quality: {quality_score['overall']}/10 ({quality_score['grade']}) - Needs improvement")
            if quality_score.get('suggestions'):
                print(f"   Suggestions: {quality_score['suggestions'][0]}")
        
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
            "escalation_triggered": should_escalate,
            "quality_score": quality_score,
            "message_count": len(self.context),
            "token_usage": self.context.get_context_window_usage(),
            "intent": intent.primary_intent,
            "specific_question": intent.specific_question
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
        """Get comprehensive conversation summary"""
        return {
            "brand_id": self.brand_id,
            "brand_name": self.brand_config.get("name"),
            "messages": len(self.context),
            "emotions_detected": self.emotions_detected,
            "total_processed": self.total_messages_processed,
            "tool_stats": self.tool_stats,
            "context_stats": self.context_stats,
            "escalation_stats": self.escalation_stats,
            "quality_stats": self.quality_stats,
            "active_topic": self.active_topic,
            "context_summary": self.context.get_conversation_summary()
        }
    
    def clear_conversation(self):
        """Clear everything"""
        self.context.clear()
        self.active_topic = None
        self.emotion_history = []
        self.quality_history = []
        self.total_messages_processed = 0
        self.emotions_detected = {k: 0 for k in self.emotions_detected}
        self.tool_stats = {k: 0 for k in self.tool_stats}
        self.context_stats = {k: 0 for k in self.context_stats}
        self.escalation_stats = {k: 0 for k in self.escalation_stats}
        self.quality_stats = {k: 0.0 for k in self.quality_stats}
    
    def __repr__(self) -> str:
        topic_info = f", topic={self.active_topic['topic_type']}" if self.active_topic else ""
        quality_info = f", quality={self.quality_stats.get('avg_overall', 0.0):.1f}"
        return f"ConversationOrchestrator(brand={self.brand_id}, messages={len(self.context)}{topic_info}{quality_info})"
