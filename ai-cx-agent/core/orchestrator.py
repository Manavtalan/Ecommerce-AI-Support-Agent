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

# Tools & Data
from core.tools.registry import ToolRegistry
from core.brands.registry import get_brand_registry
from core.config.manager import LLM_MODEL, LLM_TEMPERATURE_RESPONSE, LLM_MAX_TOKENS_RESPONSE

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
        3. [NEW] Immediate escalation check — no data gathering needed
        4. Gather needed data (order + policy)
        5. Analyze situation
        6. Generate helpful response
        7. Check smart escalation (emotion-based, repeated failures)
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
        extracted_order_id = self._extract_order_id_from_message(user_message)
        if extracted_order_id:
            self.active_order_id = extracted_order_id
            print(f"📌 Order ID captured: {self.active_order_id}")

        # === CRITICAL: HANDLE CONTEXT REPLY ===
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
        print(f"   Needs escalation: {intent.needs_escalation}")
        
        # ================================================================
        # BUG 1 FIX: IMMEDIATE ESCALATION CHECK
        # escalation_request must short-circuit here — before data gathering
        # ================================================================
        if intent.primary_intent == 'escalation_request' or intent.needs_escalation:
            print(f"   🚨 IMMEDIATE ESCALATION — intent: {intent.primary_intent}")
            self.stats['escalations'] += 1
            response = self.smart_escalation.get_escalation_message(
                intent=intent,
                escalation_reason='customer_requested' if intent.primary_intent == 'escalation_request'
                else 'high_emotion'
            )
            return self._finalize_response(response, intent, {})

        # === STEP 2: HANDLE MISSING DATA ===
        if intent.missing_data:
            if 'order_number' in intent.missing_data and self.active_order_id:
                intent.missing_data = [x for x in intent.missing_data if x != 'order_number']
                print(f"   ✅ Order ID from context: {self.active_order_id}")

            if intent.missing_data:
                print(f"   ⚠️  Still missing: {intent.missing_data}")
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

        # === STEP 5: SMART ESCALATION CHECK (emotion/failure-based) ===
        print(f"\n🚨 STEP 4: Checking smart escalation...")

        should_escalate, escalation_reason = self.smart_escalation.should_escalate(
            intent=intent,
            tool_results=data,
            conversation_history=self.conversation_history
        )

        if should_escalate:
            print(f"   ⚠️  SMART ESCALATION: {escalation_reason}")
            self.stats['escalations'] += 1
            response = self.smart_escalation.get_escalation_message(
                intent=intent,
                escalation_reason=escalation_reason
            )
            return self._finalize_response(response, intent, data)

        print(f"   ✅ No escalation needed")

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
        """Extract order ID from message - handles multiple formats"""
        patterns = [
            r'order\s*(?:id|number|#)?\s*:?\s*#?(\d{4,6})',
            r'#(\d{4,6})',
            r'\border\b.*?(\d{4,6})',
        ]

        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1)

        words = message.strip().split()
        if len(words) <= 3:
            standalone = re.search(r'\b(\d{4,6})\b', message)
            if standalone:
                return standalone.group(1)

        return None

    def _check_if_context_reply(self, message: str) -> Optional[str]:
        """Check if user is replying to a question the agent asked"""
        if not self.pending_intent:
            return None

        message_stripped = message.strip()

        if re.match(r'^#?\d{4,6}$', message_stripped):
            if 'order_number' in self.pending_intent.missing_data:
                return 'order_number_reply'

        size_patterns = ['xs', 'xm', 'xl', 'xxl', 'small', 'medium', 'large',
                         'extra small', 'extra large', 's', 'm', 'l']
        if message_stripped.lower() in size_patterns:
            if 'exchange_preference' in self.pending_intent.missing_data:
                return 'exchange_preference_reply'

        return None

    def _handle_context_reply(self, message: str, reply_type: str) -> Tuple[str, Dict]:
        """Handle when user replies with missing data — resumes pending intent"""
        intent = self.pending_intent
        self.pending_intent = None

        if reply_type == 'order_number_reply':
            order_id = re.search(r'\d{4,6}', message).group()
            self.active_order_id = order_id
            print(f"   ✅ Got order number from reply: {order_id}")
            if 'order_number' in intent.missing_data:
                intent.missing_data = [x for x in intent.missing_data if x != 'order_number']

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

        BUG 3 FIX: Always fetch order data if active_order_id exists,
        regardless of intent. Unknown/unclear intents with an order ID
        should still get order context.
        """
        data = {}

        # Intents that explicitly need order data
        order_intents = {
            'order_status_inquiry', 'order_contents_inquiry',
            'cancel_order', 'refund_request', 'exchange_request',
            'change_address', 'problem_report', 'return_request'
        }

        policy_intents = {
            'cancel_order', 'refund_request', 'return_request',
            'exchange_request', 'policy_inquiry', 'problem_report'
        }

        # BUG 3 FIX: fetch order if explicit intent needs it OR
        # if we have an active order ID (customer already gave it to us)
        needs_order = (
            intent.primary_intent in order_intents
            or (self.active_order_id is not None and intent.primary_intent == 'unknown')
            or (self.active_order_id is not None and intent.primary_intent == 'general_help')
        )

        needs_policy = intent.primary_intent in policy_intents

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
            'policy_inquiry': intent.specific_question or 'general policies shipping return refund',
            'problem_report': problem_queries.get(
                intent.problem_type,
                'customer support problem resolution policy'
            )
        }

        return intent_queries.get(intent.primary_intent, 'customer support policy')

    def _analyze_situation(self, intent: UserIntent, data: Dict) -> Dict:
        """
        Analyze the situation intelligently based on order status + policy.
        """
        analysis = {
            'can_help_directly': True,
            'recommended_action': 'provide_info',
            'options': [],
            'reasoning': '',
            'order_status': None
        }

        if data.get('order'):
            order_status = data['order'].get('status', '').lower()
            analysis['order_status'] = order_status
        else:
            order_status = None

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

            elif order_status == 'delivered':
                analysis['recommended_action'] = 'delivered_return'
                analysis['options'] = ['Return within 30 days for full refund']
                analysis['reasoning'] = 'Delivered - guide to return process'

        elif intent.primary_intent in ['return_request', 'refund_request']:
            analysis['recommended_action'] = 'guide_return'
            analysis['options'] = [
                'Prepaid return label via email',
                'Drop off at any courier partner location',
                'Full refund within 5-7 days after receipt'
            ]
            analysis['reasoning'] = 'Can process return/refund'

        elif intent.primary_intent == 'exchange_request':
            analysis['recommended_action'] = 'guide_exchange'
            analysis['options'] = [
                'Free exchange within 30 days',
                'New item shipped once return received'
            ]
            analysis['reasoning'] = 'Can process exchange'

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

        elif intent.primary_intent == 'order_status_inquiry':
            if data.get('order'):
                analysis['recommended_action'] = 'provide_status'
                analysis['reasoning'] = 'Order data available - answer specifically'
            else:
                analysis['recommended_action'] = 'order_not_found'
                analysis['can_help_directly'] = False
                analysis['reasoning'] = 'Order not found'

        elif intent.primary_intent == 'order_contents_inquiry':
            if data.get('order'):
                analysis['recommended_action'] = 'list_contents'
                analysis['reasoning'] = 'Can list order items'
            else:
                analysis['can_help_directly'] = False

        elif intent.primary_intent == 'policy_inquiry':
            if data.get('policy'):
                analysis['recommended_action'] = 'explain_policy'
                analysis['reasoning'] = 'Policy data available'
            else:
                analysis['recommended_action'] = 'general_policy'
                analysis['reasoning'] = 'Give general policy info from training'

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
        """Generate natural, helpful response using LLM with full context"""

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(intent, data, analysis, user_message)

        try:
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=LLM_TEMPERATURE_RESPONSE,
                max_tokens=LLM_MAX_TOKENS_RESPONSE
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"   ❌ LLM error: {e}")
            return self._fallback_response(intent, data, analysis)

    def _build_system_prompt(self) -> str:
        """Loads brand voice from voice_guidelines.yaml for brand-specific responses."""
        import yaml
        from pathlib import Path

        brand_name = self.brand_config.get('name', 'our company')

        voice = {}
        voice_path = Path(__file__).parent.parent / \
            "test_data" / "brands" / self.brand_id / "voice_guidelines.yaml"
        try:
            with open(voice_path, 'r') as f:
                voice = yaml.safe_load(f)
        except Exception:
            pass

        forbidden        = voice.get('forbidden_phrases', [])
        sig              = voice.get('signature_phrases', {})
        helping_phrases  = sig.get('helping', ["Let's get this sorted", "I'm on it!"])
        empathy_phrases  = sig.get('empathy', ["I hear you", "That must be frustrating"])
        closing_phrases  = sig.get('closing', ["Anything else I can help with?"])
        emoji_g          = voice.get('emoji_guidelines', {})
        preferred_emojis = " ".join(emoji_g.get('preferred_emojis', ['✨', '📦'])[:6])
        avoid_emoji_in   = ", ".join(emoji_g.get('avoid_in', ['bad_news', 'serious_issues']))
        never_emojis     = " ".join(emoji_g.get('never_use', ['😂', '😭']))
        examples         = voice.get('example_responses', {})
        greeting_ex      = "\n".join(f'  - "{e}"' for e in list(examples.get('greeting', {}).values())[:2])
        empathy_ex       = "\n".join(f'  - "{e}"' for e in list(examples.get('empathy_frustrated', {}).values())[:2])
        policy_ex        = "\n".join(f'  - "{e}"' for e in list(examples.get('policy_explanation', {}).values())[:2])
        key_facts        = voice.get('key_brand_facts', {})
        service_block    = "\n".join(f'  - {f}' for f in key_facts.get('service', []))
        usp_block        = "\n".join(f'  - {u}' for u in key_facts.get('unique_selling_points', []))
        tone_block       = "\n".join(f'  {k}: {v}' for k, v in voice.get('tone_adjustments', {}).items())
        forbidden_block  = "\n".join(f'  - "{p}"' for p in forbidden)
        helping_block    = "\n".join(f'  - "{p}"' for p in helping_phrases)
        empathy_block    = "\n".join(f'  - "{p}"' for p in empathy_phrases)
        closing_block    = "\n".join(f'  - "{p}"' for p in closing_phrases[:2])
        max_words        = voice.get('quality_standards', {}).get('response_length', {}).get('max_words', 80)
        hinglish_ok      = voice.get('language_handling', {}).get('support_hinglish', True)
        extra_banned     = [
            "I completely understand", "I appreciate your patience",
            "I understand your frustration", "Certainly!", "Absolutely!",
            "I'd be happy to assist", "I'd be glad to help", "I hope this helps!",
            "Is there anything else I can help you with today?",
            "Thank you for reaching out",
        ]
        extra_block = "\n".join(f'  - "{p}"' for p in extra_banned)

        return f"""You are a human support agent for {brand_name}.

PERSONALITY:
- Friendly professional — warm but not fake
- Direct — lead with the answer, not the acknowledgement
- Empathy through ACTIONS not performative phrases
- Conversational, casual, human — not corporate

BANNED PHRASES — NEVER USE:
From brand guidelines:
{forbidden_block}

Additional banned:
{extra_block}

SIGNATURE PHRASES — USE NATURALLY:
When helping:
{helping_block}

When showing empathy:
{empathy_block}

When closing:
{closing_block}

TONE BY SITUATION:
{tone_block}

EMOJI RULES:
Preferred: {preferred_emojis}
Avoid emojis in: {avoid_emoji_in}
Never use: {never_emojis}
Never use 😊 when customer is frustrated or upset

EXAMPLE RESPONSES — learn the voice from these:
Greetings:
{greeting_ex}

Frustrated customer:
{empathy_ex}

Policy explanation:
{policy_ex}

SPECIAL HANDLING:
- Damaged item: Lead with solution — offer refund OR replacement immediately
- Wrong item: Own it — "We sent the wrong item", fast-track the fix
- Delayed order: Acknowledge briefly, explain reason, give revised ETA

BRAND FACTS — mention when relevant:
Service:
{service_block}

Unique selling points:
{usp_block}

RESPONSE RULES:
1. MAX {max_words} words — be concise
2. Lead with ANSWER not acknowledgement
3. Use exact data — order IDs, dates, tracking numbers from the data provided
4. Number options clearly: 1. this  2. that
5. End with ONE clear next step — not a generic offer
6. Use customer's name naturally — not every sentence
7. {'Mirror Hinglish naturally if customer uses it' if hinglish_ok else 'English only'}

DATA RULES:
- Only use provided data — never invent order details or dates
- Order not found: say "I can't find that order — can you double-check the number?"
- Policy unavailable: give best answer from brand knowledge above
"""

    def _build_user_prompt(
        self,
        intent: UserIntent,
        data: Dict,
        analysis: Dict,
        user_message: str
    ) -> str:
        """Build detailed prompt with all relevant context for LLM"""

        parts = []

        parts.append(f"CUSTOMER MESSAGE: \"{user_message}\"")
        parts.append("")

        parts.append(f"INTENT: {intent.primary_intent}")
        if intent.specific_question:
            parts.append(f"SPECIFIC QUESTION: {intent.specific_question}")
        if intent.user_emotion and intent.user_emotion != 'neutral':
            parts.append(f"EMOTION: {intent.user_emotion} — show empathy through action, not phrases")
        if intent.problem_type:
            parts.append(f"PROBLEM TYPE: {intent.problem_type}")
        parts.append("")

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
                    parts.append(
                        f"    • {name}"
                        + (f" ({color}" if color else "")
                        + (f", Size {size}" if size else "")
                        + (f")" if color or size else "")
                        + f" × {qty}"
                    )

            shipping = order.get('shipping') or {}
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

        parts.append("SITUATION:")
        parts.append(f"  Action: {analysis['recommended_action']}")
        if analysis.get('options'):
            parts.append(f"  Available options:")
            for opt in analysis['options']:
                parts.append(f"    • {opt}")
        parts.append(f"  Reasoning: {analysis['reasoning']}")
        parts.append("")

        parts.append("YOUR TASK:")
        parts.append(self._get_task_instruction(intent, analysis))

        return "\n".join(parts)

    def _get_task_instruction(self, intent: UserIntent, analysis: Dict) -> str:
        """Get specific response instruction based on intent and analysis"""

        action = analysis['recommended_action']

        instructions = {
            'greeting': "Greet them briefly and ask what they need help with. One sentence max.",
            'gratitude': "Acknowledge their thanks naturally in one line and invite further questions.",
            'general_help': "Ask what they need help with today.",

            'provide_status': (
                "Answer their specific question using EXACT data provided. "
                "If they asked about delivery date, give ONLY the date. "
                "If they asked where it is, give current location. "
                "Don't dump all order info — answer what they actually asked."
            ),
            'list_contents': "List the items in their order with color, size, quantity details.",
            'order_not_found': (
                "Tell them directly you couldn't find that order and ask them "
                "to double-check the order number from their confirmation email."
            ),

            'can_cancel': (
                "Tell them you can cancel it since it hasn't shipped. "
                "Give the refund timeline. Ask if they want to go ahead."
            ),
            'shipped_alternatives': (
                "Tell them it's already shipped so cancellation isn't possible anymore, "
                "but give them the two alternatives clearly with details. "
                "Ask which they prefer."
            ),
            'delivered_return': (
                "It's already delivered so cancellation isn't an option, "
                "but walk them through the return process. Make it sound easy."
            ),

            'guide_return': (
                "Walk them through how to return step by step. "
                "Be specific about timeline and what they need to do. "
                "Offer to send a return label."
            ),

            'guide_exchange': (
                "Explain how exchange works, keep it simple. "
                "Ask what size or color they want if not already told."
            ),

            'damaged_resolution': (
                "Don't start with a long apology — start with the solution. "
                "Give them both options (refund or replacement) and ask which they want. "
                "You'll action it immediately."
            ),
            'wrong_item_resolution': (
                "Own the mistake directly — we sent the wrong item. "
                "Tell them you'll send the correct one right away. "
                "Explain what happens with the wrong item."
            ),
            'missing_package': (
                "Take it seriously. Suggest checking with neighbours/building reception. "
                "Tell them you'll file a claim and offer replacement or refund. "
                "Ask if they've checked nearby."
            ),
            'investigate_problem': (
                "Ask for details about what went wrong so you can find the best fix."
            ),

            'explain_policy': (
                "Answer the policy question directly using the policy data provided. "
                "Give specific timeframes, conditions, process steps. "
                "Be actionable, not just descriptive."
            ),
            'general_policy': (
                "Answer from your knowledge about FashionHub policies. "
                "Be specific about timeframes and how it works."
            ),

            'provide_info': "Give the most helpful response you can with what's available.",
        }

        return instructions.get(
            action,
            "Give a helpful, accurate response using available data. Be specific and direct."
        )

    def _fallback_response(self, intent: UserIntent, data: Dict, analysis: Dict) -> str:
        """Fallback when LLM fails"""

        if data.get('order'):
            order = data['order']
            status = order.get('status', 'being processed')
            order_id = order.get('order_id', '')
            return (
                f"Your order #{order_id} is currently {status}. "
                f"What else can I help you with?"
            )

        if intent.user_emotion in ['frustrated', 'angry']:
            return (
                "Something went wrong on my end — let me get you to our team "
                "who can sort this out straight away."
            )

        return "Could you give me a bit more detail so I can help you properly?"

    def _handle_missing_data(self, intent: UserIntent, user_message: str) -> str:
        """Handle missing data — ask for what we need"""

        if 'order_number' in intent.missing_data:
            intent_context = {
                'cancel_order': 'cancel that for you',
                'refund_request': 'process your refund',
                'return_request': 'help with the return',
                'exchange_request': 'sort the exchange',
                'order_status_inquiry': 'check that',
                'problem_report': 'sort this out'
            }
            action = intent_context.get(intent.primary_intent, 'help you')
            return (
                f"Sure, I can {action} — what's your order number? "
                f"You'll find it in your confirmation email, looks like #12345."
            )

        if 'exchange_preference' in intent.missing_data:
            return "What size or color would you like to exchange it for?"

        return "Could you give me a bit more detail so I can help?"

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
