"""
Intent Classifier - LLM-Powered Intelligence
Uses GPT to understand what users actually want, not keyword matching
"""

import re
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from openai import OpenAI
from dotenv import load_dotenv
from core.config.manager import LLM_MODEL, LLM_TEMPERATURE_INTENT, LLM_MAX_TOKENS_INTENT

load_dotenv()


@dataclass
class UserIntent:
    """Structured representation of what the user wants"""
    primary_intent: str
    specific_question: Optional[str]
    missing_data: List[str]
    user_emotion: str
    problem_type: Optional[str]
    needs_escalation: bool
    confidence: float


class IntentClassifier:
    """
    LLM-powered intent classifier.
    Uses GPT-4o-mini to understand intent — not keyword matching.
    
    Why LLM instead of keywords:
    - "How long does shipping take?" → NOT a greeting
    - "Do you ship to Canada?" → NOT a greeting  
    - "I ordered blue but got red" → IS a problem_report
    - "Oh great, another delay" → IS frustrated (sarcasm)
    - "When was my order shipped?" → IS order_status_inquiry
    """

    # Valid intents the classifier can return
    VALID_INTENTS = [
        'greeting',
        'order_status_inquiry',
        'order_contents_inquiry',
        'cancel_order',
        'return_request',
        'refund_request',
        'exchange_request',
        'change_address',
        'problem_report',
        'policy_inquiry',
        'product_inquiry',
        'general_help',
        'gratitude',
        'escalation_request',
        'out_of_scope',
        'unknown'
    ]

    VALID_EMOTIONS = [
        'neutral', 'frustrated', 'angry', 'worried',
        'urgent', 'happy', 'confused', 'sad', 'sarcastic'
    ]

    VALID_PROBLEMS = [
        'damaged_item', 'wrong_item', 'not_received',
        'delayed', 'missing_item', None
    ]

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.order_pattern = re.compile(r'(?:order|#)\s*#?(\d{4,6})', re.IGNORECASE)

    def analyze(
        self,
        user_message: str,
        conversation_history: List[Dict] = None,
        context: Dict[str, Any] = None
    ) -> UserIntent:
        """
        Analyze user message using LLM to determine intent.
        Falls back to rule-based if LLM fails.
        """

        # Get recent conversation context for LLM
        recent_history = self._format_history(conversation_history or [])

        # Get active order from context
        active_order = context.get('order_number') if context else None

        # Use LLM to classify
        try:
            result = self._llm_classify(user_message, recent_history, active_order)
            return self._build_intent(result, user_message, active_order)
        except Exception as e:
            print(f"   ⚠️  LLM classifier error: {e}, using fallback")
            return self._fallback_classify(user_message, active_order)

    def _llm_classify(
        self,
        message: str,
        history: str,
        active_order: Optional[str]
    ) -> Dict:
        """Use LLM to classify intent with full understanding"""

        system_prompt = f"""You are an intent classifier for a fashion e-commerce customer support agent.

Analyze the customer message and return a JSON object with these exact fields:

{{
  "primary_intent": "<intent>",
  "specific_question": "<specific aspect they want to know, or null>",
  "missing_data": ["<list of what's needed>"],
  "user_emotion": "<emotion>",
  "problem_type": "<problem type or null>",
  "needs_escalation": <true/false>,
  "confidence": <0.0-1.0>
}}

VALID INTENTS:
- greeting: hello, hi, hey
- order_status_inquiry: where is order, when arrives, shipping status, tracking, was it shipped, ship date
- order_contents_inquiry: what's in my order, what did I order
- cancel_order: wants to cancel
- return_request: wants to return item
- refund_request: wants money back
- exchange_request: wants different size/color
- change_address: wants to update delivery address
- problem_report: damaged, wrong item, not received, missing
- policy_inquiry: questions about policies, shipping cost, return window, how to return, payment methods, discounts
- product_inquiry: product availability, sizes, colors, prices
- general_help: confused, needs general assistance
- gratitude: thank you, thanks, appreciate
- escalation_request: EXPLICITLY asks for human agent, manager, or supervisor ("speak to a manager", "talk to a human", "escalate this") — expressing frustration or saying "ridiculous" alone is NOT escalation_request, use frustrated emotion instead
- out_of_scope: weather, unrelated topics, hacking
- unknown: truly unclear

VALID EMOTIONS: neutral, frustrated, angry, worried, urgent, happy, confused, sad, sarcastic

PROBLEM TYPES (only for problem_report): damaged_item, wrong_item, not_received, delayed, missing_item

MISSING DATA RULES:
- Add "order_number" ONLY if intent needs an order AND no order number exists in message OR context
- Add "exchange_preference" ONLY if intent is exchange_request (NEVER for problem_report) AND no size/color mentioned
- NEVER add "reason" for refund_request — customers don't need to justify refunds
- Do NOT add "order_number" if active_order_id is provided in context

ACTIVE ORDER CONTEXT: {active_order or 'None'}
{f'NOTE: Customer already provided order #{active_order} — do NOT add order_number to missing_data' if active_order else ''}

CRITICAL CLASSIFICATION RULES:
1. "How long does shipping take?" = policy_inquiry (NOT greeting)
2. "Do you ship to Canada?" = policy_inquiry (NOT greeting)  
3. "Can I get expedited shipping?" = policy_inquiry (NOT greeting)
4. "When was my order shipped?" = order_status_inquiry (NOT greeting)
5. "How do I return an item?" = policy_inquiry (NOT unknown)
6. "When will I get my refund?" = policy_inquiry (NOT order_status)
7. "Oh great, another delay" = order_status_inquiry + emotion: sarcastic/frustrated
8. "I ordered blue but got red" = problem_report, problem_type: wrong_item
9. "The package says delivered but I didn't get it" = problem_report, problem_type: not_received
10. "I want to speak to a manager" = escalation_request
11. "I want to speak to a human" = escalation_request
12. "You're all idiots" = problem_report + emotion: angry (NOT escalation unless they ask for manager)
13. "This is ridiculous" = order_status_inquiry + emotion: frustrated (NOT escalation_request)
14. "This is unacceptable" = emotion: frustrated (NOT escalation_request)
15. Sarcasm like "Thanks a lot" after a complaint = frustrated, NOT happy
16. "What payment methods do you accept?" = policy_inquiry
17. "Can I change delivery address?" = change_address
18. ONLY use escalation_request when customer EXPLICITLY says manager/human/supervisor/escalate
19. Frustration words like ridiculous/unacceptable/terrible = frustrated emotion, NOT escalation_request

CONVERSATION HISTORY FOR CONTEXT:
{history}"""

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Customer message: {message}"}
            ],
            temperature=LLM_TEMPERATURE_INTENT,
            max_tokens=LLM_MAX_TOKENS_INTENT,
            response_format={"type": "json_object"}
        )

        try:
            return json.loads(response.choices[0].message.content)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"   ⚠️  Intent classifier JSON parse error: {e}")
            return {
                "primary_intent": "unknown",
                "specific_question": None,
                "missing_data": [],
                "user_emotion": "neutral",
                "problem_type": None,
                "needs_escalation": False,
                "confidence": 0.3
            }

    def _build_intent(self, result: Dict, message: str, active_order: Optional[str]) -> UserIntent:
        """Build UserIntent from LLM result with validation"""

        # Validate and sanitize primary_intent
        primary_intent = result.get('primary_intent', 'unknown')
        if primary_intent not in self.VALID_INTENTS:
            primary_intent = 'unknown'

        # Validate emotion
        emotion = result.get('user_emotion', 'neutral')
        if emotion not in self.VALID_EMOTIONS:
            emotion = 'neutral'

        # Validate problem_type
        problem_type = result.get('problem_type')
        if problem_type not in self.VALID_PROBLEMS:
            problem_type = None

        # Clean missing_data — never include order_number if we have active order
        missing_data = result.get('missing_data', [])
        if active_order and 'order_number' in missing_data:
            missing_data = [x for x in missing_data if x != 'order_number']

        # Never require 'reason' for refunds
        if 'reason' in missing_data:
            missing_data = [x for x in missing_data if x != 'reason']

        # Escalation: explicit request OR very angry
        needs_escalation = result.get('needs_escalation', False)
        if primary_intent == 'escalation_request':
            needs_escalation = True
        if emotion == 'angry' and any(w in message.lower() for w in [
            'idiot', 'stupid', 'terrible', 'lawsuit', 'lawyer', 'useless', 'worst ever'
        ]):
            needs_escalation = True

        return UserIntent(
            primary_intent=primary_intent,
            specific_question=result.get('specific_question'),
            missing_data=missing_data,
            user_emotion=emotion,
            problem_type=problem_type,
            needs_escalation=needs_escalation,
            confidence=float(result.get('confidence', 0.8))
        )

    def _format_history(self, history: List[Dict]) -> str:
        """Format recent conversation history for LLM context"""
        if not history:
            return "No previous conversation."

        # Only use last 4 messages for context
        recent = history[-4:]
        lines = []
        for msg in recent:
            role = "Customer" if msg.get('role') == 'user' else "Agent"
            content = msg.get('content', '')[:150]  # Truncate long messages
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def _fallback_classify(self, message: str, active_order: Optional[str]) -> UserIntent:
        """
        Rule-based fallback when LLM fails.
        Better than the original — handles more cases correctly.
        """
        msg = message.lower().strip()
        missing = []

        # Escalation (check first)
        if any(w in msg for w in ['manager', 'supervisor', 'human', 'real person', 'escalate']):
            return UserIntent(
                primary_intent='escalation_request',
                specific_question=None,
                missing_data=[],
                user_emotion='frustrated',
                problem_type=None,
                needs_escalation=True,
                confidence=0.9
            )

        # Greeting
        if msg in ['hi', 'hello', 'hey', 'hii'] or msg.startswith(('hi ', 'hello ', 'hey ')):
            return UserIntent('greeting', None, [], 'neutral', None, False, 0.95)

        # Gratitude
        if any(w in msg for w in ['thank', 'thanks', 'appreciate', 'great help']):
            return UserIntent('gratitude', None, [], 'happy', None, False, 0.9)

        # Order status — broad patterns
        if any(w in msg for w in ['where is', 'where\'s', 'status', 'track', 'when will',
                                   'when was', 'arrive', 'shipped', 'shipping', 'delivery',
                                   'how long', 'kahan']):
            order_id = self._extract_order_id(message) or active_order
            if not order_id:
                missing.append('order_number')
            # Detect specific question
            specific = None
            if any(w in msg for w in ['when', 'arrive', 'delivery date']):
                specific = 'delivery_date'
            elif any(w in msg for w in ['where', 'location', 'kahan']):
                specific = 'current_location'
            elif 'track' in msg:
                specific = 'tracking_info'
            elif 'ship' in msg:
                specific = 'ship_date'
            return UserIntent('order_status_inquiry', specific, missing, 'neutral', None, False, 0.75)

        # Policy questions — anything asking HOW/DO/CAN about store policies
        if any(w in msg for w in ['policy', 'how do i return', 'can i return', 'how much',
                                   'do you ship', 'do you accept', 'payment', 'refund take',
                                   'return window', 'exchange policy', 'discount', 'price match']):
            return UserIntent('policy_inquiry', None, [], 'neutral', None, False, 0.8)

        # Cancellation
        if any(w in msg for w in ['cancel', 'stop order', 'don\'t want it']):
            order_id = self._extract_order_id(message) or active_order
            if not order_id:
                missing.append('order_number')
            return UserIntent('cancel_order', None, missing, 'neutral', None, False, 0.85)

        # Return
        if any(w in msg for w in ['return', 'send back', 'give back']):
            order_id = self._extract_order_id(message) or active_order
            if not order_id:
                missing.append('order_number')
            return UserIntent('return_request', None, missing, 'neutral', None, False, 0.85)

        # Refund
        if any(w in msg for w in ['refund', 'money back', 'get my money']):
            order_id = self._extract_order_id(message) or active_order
            if not order_id:
                missing.append('order_number')
            return UserIntent('refund_request', None, missing, 'neutral', None, False, 0.85)

        # Exchange
        if any(w in msg for w in ['exchange', 'swap', 'different size', 'different color']):
            order_id = self._extract_order_id(message) or active_order
            if not order_id:
                missing.append('order_number')
            if not any(w in msg for w in ['size', 'color', 'colour', 'small', 'medium', 'large']):
                missing.append('exchange_preference')
            return UserIntent('exchange_request', None, missing, 'neutral', None, False, 0.85)

        # Problem report
        if any(w in msg for w in ['damaged', 'broken', 'wrong item', 'wrong color', 'wrong size',
                                   'not received', 'didn\'t receive', 'never arrived', 'missing',
                                   'defective', 'torn', 'ripped']):
            problem = None
            if any(w in msg for w in ['damaged', 'broken', 'defective', 'torn', 'ripped']):
                problem = 'damaged_item'
            elif any(w in msg for w in ['wrong item', 'wrong color', 'wrong size', 'not what i ordered']):
                problem = 'wrong_item'
            elif any(w in msg for w in ['not received', 'didn\'t receive', 'never arrived']):
                problem = 'not_received'
            return UserIntent('problem_report', None, [], 'frustrated', problem, False, 0.8)

        # General help
        if any(w in msg for w in ['help', 'assist', 'support', 'confused']):
            return UserIntent('general_help', None, [], 'confused', None, False, 0.7)

        return UserIntent('unknown', None, [], 'neutral', None, False, 0.3)

    def _extract_order_id(self, message: str) -> Optional[str]:
        """Extract order ID from message"""
        match = self.order_pattern.search(message)
        if match:
            return match.group(1)
        # Standalone number
        words = message.strip().split()
        if len(words) <= 3:
            m = re.search(r'\b(\d{4,6})\b', message)
            if m:
                return m.group(1)
        return None
