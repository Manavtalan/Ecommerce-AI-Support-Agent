"""
Smart Escalation Manager
Escalation is LAST RESORT — only when truly needed.
"""

from typing import Dict, Optional, Tuple
from core.intelligence.intent_classifier import UserIntent


class SmartEscalationManager:
    """
    Manages escalation decisions intelligently.
    KEY PRINCIPLE: Try to help first, escalate only when necessary.
    """

    # Abusive language triggers immediate escalation
    ABUSIVE_WORDS = [
        'idiot', 'stupid', 'moron', 'useless', 'incompetent',
        'asshole', 'bastard', 'bitch', 'fuck', 'shit',
        'lawsuit', 'lawyer', 'sue', 'fraud', 'scam'
    ]

    def __init__(self):
        self.escalation_reasons = []

    def should_escalate(
        self,
        intent: UserIntent,
        tool_results: Dict,
        conversation_history: list = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if this conversation should be escalated.

        Returns: (should_escalate, reason)
        """
        self.escalation_reasons = []

        # 1. User explicitly asked for human / escalation_request intent
        if self._user_requests_human(intent):
            return True, "customer_requested"

        # 2. Abusive language detected
        if self._abusive_language_detected(intent, conversation_history):
            return True, "abusive_language"

        # 3. Severely frustrated across multiple turns
        if self._user_severely_frustrated(intent, conversation_history):
            return True, "customer_frustration"

        # 4. Critical problem + angry emotion
        if self._critical_problem_with_anger(intent):
            return True, "critical_issue"

        # 5. Multiple failed resolution attempts
        if self._multiple_failed_attempts(conversation_history):
            return True, "repeated_failure"

        return False, None

    def _user_requests_human(self, intent: UserIntent) -> bool:
        """
        BUG FIX: was checking 'human' in intent.primary_intent
        but intent is 'escalation_request', not 'human'.
        Now checks the actual intent value AND needs_escalation flag.
        """
        return (
            intent.primary_intent == 'escalation_request'
            or intent.needs_escalation
        )

    def _abusive_language_detected(
        self,
        intent: UserIntent,
        conversation_history: list
    ) -> bool:
        """
        Check for abusive language in the latest message.
        Triggers immediate escalation.
        """
        if not conversation_history:
            return False

        # Check the most recent user message only
        # BUG FIX: was using turn.get('user_message') — correct key is 'content'
        for turn in reversed(conversation_history):
            if turn.get('role') == 'user':
                message = turn.get('content', '').lower()
                return any(word in message for word in self.ABUSIVE_WORDS)

        return False

    def _user_severely_frustrated(
        self,
        intent: UserIntent,
        conversation_history: list
    ) -> bool:
        """
        Severely frustrated = angry emotion OR multiple frustration
        indicators across recent turns.

        BUG FIX: was reading turn.get('user_message') — correct key is 'content'
        BUG FIX: was only checking emotion == 'frustrated', missed 'angry'
        """
        if intent.user_emotion not in ['frustrated', 'angry']:
            return False

        # Angry alone is NOT enough — need severe keywords too
        if intent.user_emotion == 'angry' and intent.confidence < 0.5:
            return False

        # Frustrated — check if it's persistent across multiple turns
        if not conversation_history:
            return False

        severe_words = [
            'ridiculous', 'unacceptable', 'terrible', 'worst',
            'disgusting', 'pathetic', 'outrageous', 'never again'
        ]

        frustration_count = 0
        # BUG FIX: correct keys are 'role' and 'content'
        user_turns = [
            t for t in conversation_history[-6:]
            if t.get('role') == 'user'
        ]

        for turn in user_turns:
            message = turn.get('content', '').lower()
            frustration_count += sum(1 for w in severe_words if w in message)

        return frustration_count >= 2

    def _critical_problem_with_anger(self, intent: UserIntent) -> bool:
        """
        Escalate if critical problem AND customer is actually angry
        (not just frustrated — angry is a stronger signal).
        """
        critical_problems = ['damaged_item', 'wrong_item', 'not_received']
        return (
            intent.problem_type in critical_problems
            and intent.user_emotion == 'angry'
        )

    def _cannot_help(self, intent: UserIntent, tool_results: Dict) -> bool:
        """Reserved — currently we can help with everything in domain"""
        return False

    def _multiple_failed_attempts(self, conversation_history: list) -> bool:
        """
        Escalate after 3+ failed resolution attempts.

        BUG FIX: was reading turn.get('agent_response') — correct key is 'content'
        Also checks role == 'assistant' before reading content.
        """
        if not conversation_history or len(conversation_history) < 6:
            return False

        failed_attempts = 0
        failure_phrases = [
            "i don't understand",
            "could you clarify",
            "i'm not sure",
            "i cannot help",
            "can't find",
            "unable to locate"
        ]

        # BUG FIX: correct keys
        assistant_turns = [
            t for t in conversation_history[-6:]
            if t.get('role') == 'assistant'
        ]

        for turn in assistant_turns:
            response = turn.get('content', '').lower()
            if any(phrase in response for phrase in failure_phrases):
                failed_attempts += 1

        return failed_attempts >= 3

    def get_escalation_message(
        self,
        intent: UserIntent,
        escalation_reason: str
    ) -> str:
        """
        BUG FIX: Removed all banned phrases.
        - No "I completely understand your frustration"
        - No "I sincerely apologize for the inconvenience"
        - Empathy through action, not performative language
        """

        if escalation_reason == "customer_requested":
            return (
                "Sure — connecting you with our team now. "
                "They'll pick this up straight away and have full context of our chat."
            )

        elif escalation_reason == "abusive_language":
            return (
                "I want to help resolve this, but I need us to keep the conversation respectful. "
                "I'm connecting you with our senior support team who can take it from here."
            )

        elif escalation_reason == "customer_frustration":
            return (
                "This clearly hasn't been sorted the way it should've been. "
                "I'm escalating this to our senior team right now — "
                "they'll reach out to you directly and make it right."
            )

        elif escalation_reason == "critical_issue":
            return (
                "Given what's happened here, I'm passing this to our specialist team "
                "so they can handle it personally and get you a proper resolution fast."
            )

        elif escalation_reason == "repeated_failure":
            return (
                "I haven't been able to sort this the way I should have. "
                "Connecting you with our team now — they'll take it from here."
            )

        else:
            return (
                "Connecting you with our support team who can help further."
            )
