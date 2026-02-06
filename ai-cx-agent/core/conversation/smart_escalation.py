"""
Smart Escalation Manager
Escalation should be LAST RESORT, not first action
Only escalate when:
1. User explicitly asks for human
2. User is very frustrated (multiple angry phrases)
3. Critical problem AND user is frustrated
"""

from typing import Dict, Optional
from core.intelligence.intent_classifier import UserIntent


class SmartEscalationManager:
    """
    Manages escalation decisions intelligently
    KEY PRINCIPLE: Try to help first, escalate only when necessary
    """
    
    def __init__(self):
        self.escalation_reasons = []
        
    def should_escalate(
        self,
        intent: UserIntent,
        tool_results: Dict,
        conversation_history: list = None
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if this conversation should be escalated
        
        Returns:
            (should_escalate: bool, reason: str or None)
        """
        
        # Reset reasons
        self.escalation_reasons = []
        
        # Check various escalation criteria
        
        # 1. User explicitly asks for human
        if self._user_requests_human(intent):
            self.escalation_reasons.append("User requested human agent")
            return True, "customer_request"
        
        # 2. User is severely frustrated
        if self._user_severely_frustrated(intent, conversation_history):
            self.escalation_reasons.append("Customer showing high frustration")
            return True, "customer_frustration"
        
        # 3. Critical problem + frustration
        if self._critical_problem_with_frustration(intent):
            self.escalation_reasons.append("Critical issue with frustrated customer")
            return True, "critical_issue"
        
        # 4. We cannot help (no tools, no data, completely outside scope)
        if self._cannot_help(intent, tool_results):
            self.escalation_reasons.append("Unable to assist with available tools")
            return True, "capability_limitation"
        
        # 5. Multiple failed attempts
        if self._multiple_failed_attempts(conversation_history):
            self.escalation_reasons.append("Multiple unsuccessful resolution attempts")
            return True, "repeated_failure"
        
        # Otherwise, DON'T escalate - try to help!
        return False, None
    
    def _user_requests_human(self, intent: UserIntent) -> bool:
        """Check if user explicitly asks for human"""
        # This is already detected in intent classifier
        return intent.needs_escalation and "human" in str(intent.primary_intent).lower()
    
    def _user_severely_frustrated(
        self,
        intent: UserIntent,
        conversation_history: list
    ) -> bool:
        """
        Check if user is SEVERELY frustrated (not just mildly annoyed)
        Requires multiple indicators
        """
        
        if intent.user_emotion != 'frustrated':
            return False
        
        # Count frustration indicators in conversation
        frustration_count = 0
        
        severe_words = [
            'ridiculous', 'unacceptable', 'terrible', 'worst',
            'lawsuit', 'complaint', 'disgusting', 'pathetic'
        ]
        
        if conversation_history:
            for turn in conversation_history[-3:]:  # Last 3 turns
                message = turn.get('user_message', '').lower()
                frustration_count += sum(1 for word in severe_words if word in message)
        
        # Only escalate if MULTIPLE severe indicators (2+)
        return frustration_count >= 2
    
    def _critical_problem_with_frustration(self, intent: UserIntent) -> bool:
        """
        Escalate ONLY if:
        - Critical problem (damaged, wrong item, not received)
        - AND user is frustrated
        """
        
        critical_problems = ['damaged_item', 'wrong_item', 'not_received']
        
        return (
            intent.problem_type in critical_problems
            and intent.user_emotion in ['frustrated', 'angry']
        )
    
    def _cannot_help(self, intent: UserIntent, tool_results: Dict) -> bool:
        """
        Check if we genuinely cannot help
        This should be RARE - we should almost always be able to help!
        """
        
        # If we have no tools or data for this request
        # Example: User asks about competitor products, legal advice, etc.
        
        # For now, assume we can help with everything in our domain
        return False
    
    def _multiple_failed_attempts(self, conversation_history: list) -> bool:
        """
        Escalate if we've tried to help multiple times and failed
        """
        
        if not conversation_history or len(conversation_history) < 4:
            return False
        
        # Count how many times we've asked for clarification or said we can't help
        failed_attempts = 0
        
        for turn in conversation_history[-4:]:
            response = turn.get('agent_response', '').lower()
            if any(phrase in response for phrase in [
                "i don't understand",
                "could you clarify",
                "i'm not sure",
                "i cannot help"
            ]):
                failed_attempts += 1
        
        # Escalate after 3+ failed attempts
        return failed_attempts >= 3
    
    def get_escalation_message(
        self,
        intent: UserIntent,
        escalation_reason: str
    ) -> str:
        """
        Generate appropriate escalation message
        """
        
        empathy = ""
        if intent.user_emotion == 'frustrated':
            empathy = "I completely understand your frustration, and I'm sorry we couldn't resolve this to your satisfaction. "
        elif intent.user_emotion == 'worried':
            empathy = "I understand this is concerning for you. "
        
        if escalation_reason == "customer_request":
            return (
                f"{empathy}I'm connecting you with our support team who can provide "
                "more personalized assistance. They'll be with you shortly!"
            )
        
        elif escalation_reason == "customer_frustration":
            return (
                "I sincerely apologize that we haven't been able to resolve this to your satisfaction. "
                "Let me connect you with a senior support specialist who can give this their immediate attention."
            )
        
        elif escalation_reason == "critical_issue":
            return (
                f"{empathy}Given the nature of this issue, I want to make sure you get the best possible resolution. "
                "Let me connect you with our support team who can handle this personally."
            )
        
        elif escalation_reason == "capability_limitation":
            return (
                "I want to make sure you get the help you need. Let me connect you with "
                "a specialist who can assist you better with this specific request."
            )
        
        elif escalation_reason == "repeated_failure":
            return (
                "I apologize that I haven't been able to help you effectively so far. "
                "Let me connect you with our support team who can provide more comprehensive assistance."
            )
        
        else:
            return (
                "Let me connect you with our support team who can assist you further."
            )
    
    def should_try_to_help_first(self, intent: UserIntent) -> bool:
        """
        Determine if we should attempt to help before escalating
        Returns True for most cases - we want to try helping!
        """
        
        # We should try to help for these intents
        helpful_intents = [
            'order_status_inquiry',
            'order_contents_inquiry',
            'cancel_order',
            'refund_request',
            'exchange_request',
            'change_address',
            'problem_report',
            'policy_inquiry',
            'product_inquiry'
        ]
        
        return intent.primary_intent in helpful_intents
    
    def get_help_attempt_context(self, intent: UserIntent) -> Dict[str, str]:
        """
        Get context for attempting to help
        Returns what the agent should try to do before escalating
        """
        
        if intent.primary_intent == 'cancel_order':
            return {
                'action': 'check_order_status',
                'help_message': 'Check if order shipped. If not, cancel it. If yes, offer refuse delivery or return options.'
            }
        
        elif intent.primary_intent == 'refund_request':
            return {
                'action': 'check_order_status',
                'help_message': 'Explain refund process based on order status. Guide through return if needed.'
            }
        
        elif intent.primary_intent == 'problem_report':
            return {
                'action': 'offer_solution',
                'help_message': 'Show high empathy, offer replacement or refund. Only escalate if customer insists.'
            }
        
        return {}


# Convenience function
def check_escalation(intent: UserIntent, tool_results: Dict, history: list = None) -> tuple[bool, Optional[str]]:
    """
    Convenience function to check if escalation is needed
    
    Usage:
        should_escalate, reason = check_escalation(intent, tool_results, history)
        if should_escalate:
            return escalation_message
    """
    manager = SmartEscalationManager()
    return manager.should_escalate(intent, tool_results, history)
