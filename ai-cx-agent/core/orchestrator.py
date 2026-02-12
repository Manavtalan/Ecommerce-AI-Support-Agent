"""
Intelligent Conversation Orchestrator
Production-grade AI agent with policy-aware responses
"""

from typing import Dict, Tuple, Optional, List
from datetime import datetime
from openai import OpenAI
import os
import re

# Core components
from core.conversation.context import ConversationContext
from core.intelligence.intent_classifier import IntentClassifier, UserIntent
from core.conversation.smart_escalation import SmartEscalationManager
from core.emotion.detector import EmotionDetector

# Tools & Data
from core.tools.registry import ToolRegistry
from core.brands.registry import get_brand_registry

from dotenv import load_dotenv
load_dotenv()


class ConversationOrchestrator:
    """
    Intelligent AI Agent Orchestrator

    Philosophy:
    1. Understand intent deeply (not keywords)
    2. Gather all needed data (order + policy)
    3. Analyze situation intelligently
    4. Provide helpful, policy-based responses
    5. Escalate only when truly needed
    """

    def __init__(self, brand_id: str = "fashionhub"):
        """Initialize intelligent orchestrator"""

        # Validate brand
        registry = get_brand_registry()
        if not registry.validate_brand_id(brand_id):
            raise ValueError(f"Invalid brand_id: {brand_id}")

        self.brand_id = brand_id
        self.brand_config = registry.get_brand_by_id(brand_id)

        # Intelligence components
        self.intent_classifier = IntentClassifier()
        self.smart_escalation = SmartEscalationManager()

        # Context & Memory
        self.context = ConversationContext()
        self.conversation_history = []

        # Tools
        self.tools = ToolRegistry(brand_id)

        # RAG availability
        try:
            from core.rag.retriever import KnowledgeRetriever
            self.retriever = KnowledgeRetriever(brand_id)
            self.rag_available = True
        except Exception:
            self.retriever = None
            self.rag_available = False

        # LLM for response generation
        self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Active conversation state - CRITICAL for context retention
        self.active_order_id = None
        self.pending_intent = None  # Stores intent when waiting for more info

        # Stats
        self.stats = {
            'messages_processed': 0,
            'escalations': 0,
            'policies_used': 0,
            'direct_help': 0
        }

        print(f"✅ Intelligent Agent initialized for {self.brand_config['name']}")

    def process_message(self, user_message: str) -> Tuple[str, Dict]:
        """
        Main intelligence flow

        Flow:
        1. Extract any order number from message
        2. Understand intent (with full context awareness)
        3. Gather needed data (order + policy)
        4. Analyze situation
        5. Generate helpful response
        6. Check if escalation needed
        """

        self.stats['messages_processed'] += 1

        # Add to memory
        self.context.add_user_message(user_message)
        self.conversation_history.append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now()
        })

        print(f"\n{'='*70}")
        print(f"👤 User: {user_message}")
        print(f"{'='*70}\n")

        # === CRITICAL: EXTRACT ORDER NUMBER FIRST ===
        # Do this BEFORE intent classification so context is available
        extracted_order_id = self._extract_order_id_from_message(user_message)
        if extracted_order_id:
            self.active_order_id = extracted_order_id
            print(f"📌 Order ID captured: {self.active_order_id}")

        # === CRITICAL: HANDLE CONTEXT REPLY ===
        # User replied with just an order number or short answer
        # after agent asked for more info
        context_response = self._check_if_context_reply(user_message)
        if context_response:
            print(f"🔄 Context reply detected - resuming pending intent")
            return self._handle_context_reply(user_message, context_response)

        # === STEP 1: UNDERSTAND INTENT ===
        print("🧠 STEP 1: Analyzing intent...")

        intent = self.intent_classifier.analyze(
            user_message=user_message,
            conversation_history=self.conversation_history,
            context={'order_number': self.active_order_id}
        )

        print(f"   Intent: {intent.primary_intent}")
        print(f"   Specific: {intent.specific_question}")
        print(f"   Emotion: {intent.user_emotion}")
        print(f"   Missing: {intent.missing_data}")

        # === STEP 2: HANDLE MISSING DATA ===
        # Only ask for order number if we truly don't have it
        if intent.missing_data:
            # Double check - do we already have order ID in context?
            if 'order_number' in intent.missing_data and self.active_order_id:
                # We have it! Remove from missing
                intent.missing_data.remove('order_number')
                print(f"   ✅ Order ID from context: {self.active_order_id}")

            # Still missing data?
            if intent.missing_data:
                print(f"   ⚠️  Still missing: {intent.missing_data}")
                # Store pending intent so we can resume after user provides info
                self.pending_intent = intent
                response = self._handle_missing_data(intent, user_message)
                return self._finalize_response(response, intent, {})

        # === STEP 3: GATHER REQUIRED DATA ===
        print(f"\n📦 STEP 2: Gathering data...")
        data = self._gather_data(intent, user_message)

        print(f"   Order data: {'✅' if data.get('order') else '❌'}")
        print(f"   Policy data: {'✅' if data.get('policy') else '❌'}")

        # === STEP 4: ANALYZE SITUATION ===
        print(f"\n🔍 STEP 3: Analyzing situation...")
        analysis = self._analyze_situation(intent, data)

        print(f"   Can help: {analysis['can_help_directly']}")
        print(f"   Action: {analysis['recommended_action']}")

        # === STEP 5: CHECK ESCALATION ===
        print(f"\n🚨 STEP 4: Checking escalation...")

        should_escalate, escalation_reason = self.smart_escalation.should_escalate(
            intent=intent,
            tool_results=data,
            conversation_history=self.conversation_history
        )

        if should_escalate:
            print(f"   ⚠️  ESCALATION: {escalation_reason}")
            self.stats['escalations'] += 1
            response = self.smart_escalation.get_escalation_message(
                intent=intent,
                escalation_reason=escalation_reason
            )
            return self._finalize_response(response, intent, data)

        print(f"   ✅ No escalation - agent will help")

        # === STEP 6: GENERATE INTELLIGENT RESPONSE ===
        print(f"\n✨ STEP 5: Generating response...")

        if analysis['can_help_directly']:
            self.stats['direct_help'] += 1
        if data.get('policy'):
            self.stats['policies_used'] += 1

        response = self._generate_intelligent_response(
            intent=intent,
            data=data,
            analysis=analysis,
            user_message=user_message
        )

        return self._finalize_response(response, intent, data)

    def _extract_order_id_from_message(self, message: str) -> Optional[str]:
        """
        Extract order ID from message - handles multiple formats:
        - "order 12345"
        - "order #12345"
        - "#12345"
        - just "12345" (5 digit number)
        - "order id: 12345"
        - "order number 12345"
        """
        # Pattern 1: explicit order reference
        patterns = [
            r'order\s*(?:id|number|#)?\s*:?\s*#?(\d{4,6})',  # "order 12345", "order id: 12345"
            r'#(\d{4,6})',  # "#12345"
            r'\border\b.*?(\d{4,6})',  # "my order 12345"
        ]

        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1)

        # Pattern 2: standalone number (only if short message suggesting it's an order reply)
        words = message.strip().split()
        if len(words) <= 3:  # Short message
            standalone = re.search(r'\b(\d{4,6})\b', message)
            if standalone:
                return standalone.group(1)

        return None

    def _check_if_context_reply(self, message: str) -> Optional[str]:
        """
        Check if user is replying to a question the agent asked.
        Returns the type of context reply, or None.

        Examples:
        - Agent asked "What's your order number?" → User replies "12345"
        - Agent asked "What size?" → User replies "Large"
        """
        if not self.pending_intent:
            return None

        message_stripped = message.strip()

        # Check if this looks like an order number reply
        if re.match(r'^#?\d{4,6}$', message_stripped):
            if 'order_number' in self.pending_intent.missing_data:
                return 'order_number_reply'

        # Check if this looks like a size reply
        size_patterns = ['xs', 'xm', 'xl', 'xxl', 'small', 'medium', 'large',
                         'extra small', 'extra large', 's', 'm', 'l']
        if message_stripped.lower() in size_patterns:
            if 'exchange_preference' in self.pending_intent.missing_data:
                return 'exchange_preference_reply'

        return None

    def _handle_context_reply(self, message: str, reply_type: str) -> Tuple[str, Dict]:
        """
        Handle when user replies to agent's question with missing data.
        Resumes the pending intent with the new information.
        """
        intent = self.pending_intent
        self.pending_intent = None  # Clear pending

        if reply_type == 'order_number_reply':
            # Extract and store order number
            order_id = re.search(r'\d{4,6}', message).group()
            self.active_order_id = order_id
            print(f"   ✅ Got order number from reply: {order_id}")

            # Remove from missing data and continue
            if 'order_number' in intent.missing_data:
                intent.missing_data.remove('order_number')

        # Now gather data and continue normally
        data = self._gather_data(intent, message)
        analysis = self._analyze_situation(intent, data)

        should_escalate, escalation_reason = self.smart_escalation.should_escalate(
            intent=intent,
            tool_results=data,
            conversation_history=self.conversation_history
        )

        if should_escalate:
            self.stats['escalations'] += 1
            response = self.smart_escalation.get_escalation_message(intent, escalation_reason)
        else:
            if analysis['can_help_directly']:
                self.stats['direct_help'] += 1
            if data.get('policy'):
                self.stats['policies_used'] += 1

            response = self._generate_intelligent_response(
                intent=intent,
                data=data,
                analysis=analysis,
                user_message=message
            )

        return self._finalize_response(response, intent, data)

    def _gather_data(self, intent: UserIntent, user_message: str) -> Dict:
        """
        Gather all data needed for this intent.
        Always fetches BOTH order data AND relevant policy together.
        """
        data = {}

        needs_order = intent.primary_intent in [
            'order_status_inquiry', 'order_contents_inquiry',
            'cancel_order', 'refund_request', 'exchange_request',
            'change_address', 'problem_report', 'return_request'
        ]

        needs_policy = intent.primary_intent in [
            'cancel_order', 'refund_request', 'return_request',
            'exchange_request', 'policy_inquiry', 'problem_report'
        ]

        # === GET ORDER DATA ===
        if needs_order and self.active_order_id:
            print(f"   Fetching order {self.active_order_id}...")
            order_result = self.tools.execute_with_retry(
                'get_order_status',
                order_id=self.active_order_id
            )

            if order_result['success']:
                data['order'] = order_result['data']
                print(f"   ✅ Order loaded: status={order_result['data'].get('status')}")
            else:
                print(f"   ❌ Order not found")

        elif needs_order and not self.active_order_id:
            print(f"   ⚠️  Need order ID but none available")

        # === GET POLICY DATA ===
        if needs_policy and self.rag_available:
            policy_query = self._build_policy_query(intent)
            print(f"   Searching policy: '{policy_query}'...")

            policy_result = self.tools.execute_with_retry(
                'search_knowledge',
                query=policy_query
            )

            if policy_result['success']:
                data['policy'] = policy_result['data']
                print(f"   ✅ Policy loaded")
            else:
                print(f"   ⚠️  Policy not found in knowledge base")

        return data

    def _build_policy_query(self, intent: UserIntent) -> str:
        """Build appropriate policy search query based on intent"""

        problem_queries = {
            'damaged_item': 'damaged defective product refund replacement policy',
            'wrong_item': 'wrong incorrect item received policy',
            'not_received': 'package not received missing lost order policy',
            'delayed': 'delayed late delivery order policy'
        }

        intent_queries = {
            'cancel_order': 'order cancellation policy cancel refund',
            'refund_request': 'refund policy money back how to get refund',
            'return_request': 'return policy how to return item',
            'exchange_request': 'exchange policy size color change swap',
            'change_address': 'change delivery address policy',
            'policy_inquiry': 'general policies shipping return refund',
            'problem_report': problem_queries.get(
                intent.problem_type,
                'customer support problem resolution policy'
            )
        }

        return intent_queries.get(intent.primary_intent, 'customer support policy')

    def _analyze_situation(self, intent: UserIntent, data: Dict) -> Dict:
        """
        Analyze the situation intelligently based on order status + policy.
        Returns what action to take and what options are available.
        """

        analysis = {
            'can_help_directly': True,  # Default to CAN help
            'recommended_action': 'provide_info',
            'options': [],
            'reasoning': '',
            'order_status': None
        }

        # Get order status if available
        if data.get('order'):
            order_status = data['order'].get('status', '').lower()
            analysis['order_status'] = order_status
        else:
            order_status = None

        # === CANCELLATION ===
        if intent.primary_intent == 'cancel_order':
            if not order_status:
                analysis['recommended_action'] = 'ask_order_status'
                analysis['reasoning'] = 'Need order to check if cancellable'
                return analysis

            if order_status in ['pending', 'processing', 'confirmed', 'unfulfilled']:
                analysis['recommended_action'] = 'can_cancel'
                analysis['options'] = ['Full refund within 5-7 business days']
                analysis['reasoning'] = 'Order not shipped - cancellation possible'

            elif order_status in ['shipped', 'in_transit', 'out_for_delivery',
                                   'fulfilled', 'partially_fulfilled']:
                analysis['recommended_action'] = 'shipped_alternatives'
                analysis['options'] = [
                    'Refuse the delivery - automatic full refund',
                    'Accept and return within 30 days for full refund'
                ]
                analysis['reasoning'] = 'Already shipped - offer alternatives'

            elif order_status in ['delivered']:
                analysis['recommended_action'] = 'delivered_return'
                analysis['options'] = ['Return within 30 days for full refund']
                analysis['reasoning'] = 'Delivered - guide to return process'

        # === RETURN ===
        elif intent.primary_intent in ['return_request', 'refund_request']:
            analysis['recommended_action'] = 'guide_return'
            analysis['options'] = [
                'Prepaid return label via email',
                'Drop off at any courier partner location',
                'Full refund within 5-7 days after receipt'
            ]
            analysis['reasoning'] = 'Can process return/refund'

        # === EXCHANGE ===
        elif intent.primary_intent == 'exchange_request':
            analysis['recommended_action'] = 'guide_exchange'
            analysis['options'] = [
                'Free exchange within 30 days',
                'New item shipped once return received'
            ]
            analysis['reasoning'] = 'Can process exchange'

        # === PROBLEM REPORT ===
        elif intent.primary_intent == 'problem_report':
            if intent.problem_type == 'damaged_item':
                analysis['recommended_action'] = 'damaged_resolution'
                analysis['options'] = [
                    'Full refund - no return needed',
                    'Free replacement with express shipping'
                ]
                analysis['reasoning'] = 'Damaged item - immediate resolution'

            elif intent.problem_type == 'wrong_item':
                analysis['recommended_action'] = 'wrong_item_resolution'
                analysis['options'] = [
                    'Correct item shipped immediately',
                    'Full refund'
                ]
                analysis['reasoning'] = 'Wrong item sent - fix immediately'

            elif intent.problem_type == 'not_received':
                analysis['recommended_action'] = 'missing_package'
                analysis['options'] = [
                    'File missing package claim',
                    'Replacement or full refund'
                ]
                analysis['reasoning'] = 'Package not received - investigate'

            else:
                analysis['recommended_action'] = 'investigate_problem'
                analysis['reasoning'] = 'General problem - gather details'

        # === ORDER STATUS ===
        elif intent.primary_intent == 'order_status_inquiry':
            if data.get('order'):
                analysis['recommended_action'] = 'provide_status'
                analysis['reasoning'] = 'Order data available - answer specifically'
            else:
                analysis['recommended_action'] = 'order_not_found'
                analysis['can_help_directly'] = False
                analysis['reasoning'] = 'Order not found'

        # === ORDER CONTENTS ===
        elif intent.primary_intent == 'order_contents_inquiry':
            if data.get('order'):
                analysis['recommended_action'] = 'list_contents'
                analysis['reasoning'] = 'Can list order items'
            else:
                analysis['can_help_directly'] = False

        # === POLICY QUESTION ===
        elif intent.primary_intent == 'policy_inquiry':
            if data.get('policy'):
                analysis['recommended_action'] = 'explain_policy'
                analysis['reasoning'] = 'Policy data available'
            else:
                analysis['recommended_action'] = 'general_policy'
                analysis['reasoning'] = 'Give general policy info'

        # === GREETING / GRATITUDE ===
        elif intent.primary_intent in ['greeting', 'gratitude', 'general_help']:
            analysis['recommended_action'] = intent.primary_intent
            analysis['reasoning'] = 'Social interaction'

        return analysis

    def _generate_intelligent_response(
        self,
        intent: UserIntent,
        data: Dict,
        analysis: Dict,
        user_message: str
    ) -> str:
        """
        Generate natural, helpful response using LLM with full context.
        """

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(intent, data, analysis, user_message)

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"   ❌ LLM error: {e}")
            return self._fallback_response(intent, data, analysis)

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM"""
        brand_name = self.brand_config.get('name', 'our company')
        tone = self.brand_config.get('voice', {}).get('tone', 'friendly and professional')

        return f"""You are an intelligent customer support agent for {brand_name}.

CORE MISSION: Help customers resolve their issues using real order data and policy information.

CRITICAL RULES:
1. Use ONLY the data provided - never invent order details, dates, or policies
2. Be SPECIFIC - use exact order IDs, dates, tracking numbers from the data
3. Be HELPFUL - explain what you CAN do, offer options, guide next steps
4. Be EMPATHETIC - acknowledge frustration before providing solutions
5. Be CONCISE - answer what was asked, don't dump all available data
6. Use policy information to EXPLAIN options, not just say "contact support"

RESPONSE FORMAT:
- If customer is frustrated: Start with empathy, then solution
- If offering options: Number them clearly (1. option one  2. option two)
- Always end with a clear next step or question
- Keep response under 200 words unless detail is truly needed

Brand tone: {tone}"""

    def _build_user_prompt(
        self,
        intent: UserIntent,
        data: Dict,
        analysis: Dict,
        user_message: str
    ) -> str:
        """Build detailed prompt with all relevant context for LLM"""

        parts = []

        # Customer's message
        parts.append(f"CUSTOMER MESSAGE: \"{user_message}\"")
        parts.append("")

        # Intent analysis
        parts.append(f"INTENT: {intent.primary_intent}")
        if intent.specific_question:
            parts.append(f"SPECIFIC QUESTION: {intent.specific_question}")
        if intent.user_emotion and intent.user_emotion != 'neutral':
            parts.append(f"EMOTION: {intent.user_emotion} ← Show empathy first!")
        if intent.problem_type:
            parts.append(f"PROBLEM TYPE: {intent.problem_type}")
        parts.append("")

        # Order data - structured and clean
        if data.get('order'):
            order = data['order']
            parts.append("ORDER DATA:")
            parts.append(f"  Order #: {order.get('order_id')}")
            parts.append(f"  Status: {order.get('status', 'unknown').upper()}")
            parts.append(f"  Customer: {order.get('customer_name', 'N/A')}")
            parts.append(f"  Date: {order.get('order_date', 'N/A')}")

            items = order.get('items', [])
            if items:
                parts.append(f"  Items:")
                for item in items:
                    name = item.get('name', 'Item')
                    color = item.get('color', '')
                    size = item.get('size', '')
                    qty = item.get('quantity', 1)
                    parts.append(f"    • {name}"
                                 + (f" ({color}" if color else "")
                                 + (f", Size {size}" if size else "")
                                 + (f")" if color or size else "")
                                 + f" × {qty}")

            shipping = order.get('shipping', {})
            if shipping:
                if shipping.get('tracking_number'):
                    parts.append(f"  Tracking: {shipping.get('tracking_number')}")
                if shipping.get('courier'):
                    parts.append(f"  Courier: {shipping.get('courier')}")
                if shipping.get('estimated_delivery'):
                    parts.append(f"  Est. Delivery: {shipping.get('estimated_delivery')}")
                if shipping.get('current_location'):
                    parts.append(f"  Current Location: {shipping.get('current_location')}")
                if shipping.get('last_update'):
                    parts.append(f"  Last Update: {shipping.get('last_update')}")
            parts.append("")

        # Policy data - extract text cleanly
        if data.get('policy'):
            policy = data['policy']
            parts.append("RELEVANT POLICY:")

            if isinstance(policy, dict) and 'results' in policy:
                for result in policy['results'][:2]:
                    text = result.get('text', '').strip()
                    if text:
                        parts.append(f"  {text[:400]}")
            elif isinstance(policy, str):
                parts.append(f"  {policy[:400]}")
            parts.append("")

        # Situation analysis
        parts.append("SITUATION:")
        parts.append(f"  Action: {analysis['recommended_action']}")
        if analysis.get('options'):
            parts.append(f"  Available options:")
            for opt in analysis['options']:
                parts.append(f"    • {opt}")
        parts.append(f"  Reasoning: {analysis['reasoning']}")
        parts.append("")

        # Specific instruction
        parts.append("YOUR TASK:")
        parts.append(self._get_task_instruction(intent, analysis))

        return "\n".join(parts)

    def _get_task_instruction(self, intent: UserIntent, analysis: Dict) -> str:
        """Get specific response instruction based on intent and analysis"""

        action = analysis['recommended_action']

        instructions = {
            # Greetings
            'greeting': "Greet the customer warmly and ask how you can help them today.",
            'gratitude': "Respond warmly to their thanks and invite further questions.",
            'general_help': "Ask what they need help with today.",

            # Order status
            'provide_status': (
                f"Answer their specific question about the order using EXACT data provided. "
                f"If they asked about delivery date, give ONLY the date. "
                f"If they asked where it is, give the current location. "
                f"Don't dump all order info - answer what they actually asked."
            ),
            'list_contents': "List the items in their order with color, size, quantity details.",
            'order_not_found': "Apologize that you couldn't find the order and ask them to verify the number.",

            # Cancellation
            'can_cancel': (
                "Tell them the good news - you CAN cancel it since it hasn't shipped yet. "
                "Explain the refund timeline from the policy. Ask if they want to proceed."
            ),
            'shipped_alternatives': (
                "Explain you can't cancel since it's already shipped, "
                "but present the alternatives clearly with full details from the policy. "
                "Ask which option they prefer."
            ),
            'delivered_return': (
                "Explain it's been delivered so cancellation isn't possible, "
                "but guide them through the return process using the policy details."
            ),

            # Returns & refunds
            'guide_return': (
                "Walk them through exactly how to return their item step by step. "
                "Use the policy to explain the timeline and any requirements. "
                "Offer to send a return label."
            ),

            # Exchange
            'guide_exchange': (
                "Explain how the exchange process works using the policy. "
                "Ask what size or color they want. Make it sound easy and hassle-free."
            ),

            # Problems
            'damaged_resolution': (
                "Start with a genuine apology for receiving a damaged item. "
                "Present both options (refund or replacement) clearly. "
                "Use the policy to confirm what they're entitled to. "
                "Ask which they prefer and say you'll action it immediately."
            ),
            'wrong_item_resolution': (
                "Sincerely apologize for sending the wrong item - it's our mistake. "
                "Tell them you'll send the correct item right away. "
                "Explain they can keep or return the wrong item per the policy."
            ),
            'missing_package': (
                "Show empathy and take the issue seriously. "
                "Suggest checking with neighbors/building reception first. "
                "Explain you'll file a claim and offer replacement or refund. "
                "Ask if they've checked nearby locations."
            ),
            'investigate_problem': (
                "Show empathy and ask for more details about what went wrong "
                "so you can find the best resolution for them."
            ),

            # Policy
            'explain_policy': (
                "Answer their policy question directly and clearly using the policy data provided. "
                "Give specific details (timeframes, conditions, process steps). "
                "Don't just summarize - give them actionable information."
            ),
            'general_policy': (
                "Give them helpful information about the policy from your knowledge. "
                "Be specific about timeframes and processes."
            ),

            # Default
            'provide_info': "Provide the most helpful response you can with the available information.",
        }

        return instructions.get(
            action,
            "Provide a helpful, accurate response using the data available. Be specific and actionable."
        )

    def _fallback_response(self, intent: UserIntent, data: Dict, analysis: Dict) -> str:
        """Fallback when LLM fails - still intelligent based on context"""

        if data.get('order'):
            order = data['order']
            status = order.get('status', 'being processed')
            order_id = order.get('order_id', '')
            return (
                f"Your order #{order_id} is currently {status}. "
                f"If you need more help with this order, I'm here to assist!"
            )

        if intent.user_emotion == 'frustrated':
            return (
                "I understand your frustration and I sincerely want to help. "
                "Let me connect you with our support team who can resolve this right away."
            )

        return (
            "I want to make sure you get accurate help. "
            "Could you provide a bit more detail about what you need?"
        )

    def _handle_missing_data(self, intent: UserIntent, user_message: str) -> str:
        """Handle missing data - ask for what we need"""

        if 'order_number' in intent.missing_data:
            # Tailor question to their intent
            intent_context = {
                'cancel_order': 'cancel',
                'refund_request': 'process your refund',
                'return_request': 'help with the return',
                'exchange_request': 'process the exchange',
                'order_status_inquiry': 'check the status',
                'problem_report': 'resolve this issue'
            }
            action = intent_context.get(intent.primary_intent, 'help you')
            return (
                f"I'd be happy to {action} for you! 😊\n\n"
                f"Could you please share your order number? "
                f"You can find it in your confirmation email - it looks like #12345."
            )

        if 'exchange_preference' in intent.missing_data:
            return (
                "I can help you with the exchange! 😊\n\n"
                "What size or color would you like to exchange it for?"
            )

        return "I'd be happy to help! Could you provide a bit more detail?"

    def _finalize_response(
        self,
        response: str,
        intent: UserIntent,
        data: Dict
    ) -> Tuple[str, Dict]:
        """Add response to context and return with metadata"""

        self.context.add_assistant_message(response)
        self.conversation_history.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now()
        })

        metadata = {
            'brand_id': self.brand_id,
            'intent': intent.primary_intent,
            'specific_question': intent.specific_question,
            'emotion': intent.user_emotion,
            'problem_type': intent.problem_type,
            'had_order_data': bool(data.get('order')),
            'had_policy_data': bool(data.get('policy')),
            'active_order': self.active_order_id,
            'stats': self.stats
        }

        print(f"\n✅ Response generated")
        print(f"{'='*70}\n")

        return response, metadata

    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        return {
            **self.stats,
            'context_usage': self.context.get_context_window_usage(),
            'active_order': self.active_order_id
        }

    def clear_conversation(self):
        """Clear all conversation state"""
        self.context.clear()
        self.conversation_history = []
        self.active_order_id = None
        self.pending_intent = None

    def __repr__(self) -> str:
        return (
            f"IntelligentOrchestrator("
            f"brand={self.brand_id}, "
            f"messages={self.stats['messages_processed']}, "
            f"active_order={self.active_order_id})"
        )
