"""
Intent Classifier - The Brain of the AI Agent
Analyzes user messages to understand what they want and how to respond
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class UserIntent:
    """Structured representation of what the user wants"""
    primary_intent: str  # order_status, cancel_order, refund, etc.
    specific_question: Optional[str]  # delivery_date, tracking, contents, etc.
    missing_data: List[str]  # ['order_number', 'reason', etc.]
    user_emotion: str  # neutral, frustrated, happy, worried, angry
    problem_type: Optional[str]  # damaged, wrong_item, not_received, late
    needs_escalation: bool
    confidence: float  # 0.0 to 1.0


class IntentClassifier:
    """
    Analyzes user messages to determine intent, emotion, and required actions
    This is the 'intelligence' that makes the agent smart
    """
    
    def __init__(self):
        self.order_number_pattern = re.compile(r'(?:order|#)\s*(\d{5,})')
        
    def analyze(
        self, 
        user_message: str, 
        conversation_history: List[Dict] = None,
        context: Dict[str, Any] = None
    ) -> UserIntent:
        """
        Main analysis method - determines what user wants
        
        Args:
            user_message: Current user message
            conversation_history: Previous messages in conversation
            context: Current conversation context (order_number, etc.)
            
        Returns:
            UserIntent with all detected information
        """
        message_lower = user_message.lower()
        
        # Extract order number if present
        order_number = self._extract_order_number(user_message, context)
        
        # Detect primary intent
        primary_intent = self._detect_primary_intent(message_lower)
        
        # Detect specific question within intent
        specific_question = self._detect_specific_question(message_lower, primary_intent)
        
        # Detect missing data
        missing_data = self._detect_missing_data(primary_intent, order_number, message_lower)
        
        # Detect user emotion
        emotion = self._detect_emotion(message_lower, conversation_history)
        
        # Detect problem type (if any)
        problem_type = self._detect_problem_type(message_lower)
        
        # Determine if escalation needed
        needs_escalation = self._should_escalate(
            primary_intent, 
            problem_type, 
            emotion,
            message_lower
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(message_lower, primary_intent)
        
        return UserIntent(
            primary_intent=primary_intent,
            specific_question=specific_question,
            missing_data=missing_data,
            user_emotion=emotion,
            problem_type=problem_type,
            needs_escalation=needs_escalation,
            confidence=confidence
        )
    
    def _extract_order_number(self, message: str, context: Dict) -> Optional[str]:
        """Extract order number from message or context"""
        # Check context first (from previous turns)
        if context and 'order_number' in context:
            return context['order_number']
        
        # Try to extract from current message
        match = self.order_number_pattern.search(message)
        if match:
            return match.group(1)
        
        # Check for just numbers (might be order number)
        if message.strip().isdigit() and len(message.strip()) >= 5:
            return message.strip()
        
        return None
    
    def _detect_primary_intent(self, message_lower: str) -> str:
        """Detect the main thing user wants to do"""
        
        # Order status inquiry
        if any(phrase in message_lower for phrase in [
            'where is', 'where\'s', 'kahan hai', 'status', 'track',
            'when will', 'has it shipped', 'is it shipped'
        ]):
            return 'order_status_inquiry'
        
        # Order contents
        if any(phrase in message_lower for phrase in [
            'what\'s in', 'what is in', 'contents', 'what did i order'
        ]):
            return 'order_contents_inquiry'
        
        # Cancellation
        if any(phrase in message_lower for phrase in [
            'cancel', 'don\'t want', 'stop order'
        ]):
            return 'cancel_order'
        
        # Refund
        if any(phrase in message_lower for phrase in [
            'refund', 'money back', 'get my money'
        ]):
            return 'refund_request'
        
        # Exchange
        if any(phrase in message_lower for phrase in [
            'exchange', 'swap', 'different size', 'different color'
        ]):
            return 'exchange_request'
        
        # Change address
        if any(phrase in message_lower for phrase in [
            'change address', 'update address', 'different address', 'wrong address'
        ]):
            return 'change_address'
        
        # Problem reports
        if any(phrase in message_lower for phrase in [
            'damaged', 'broken', 'defective', 'wrong item', 'not received',
            'didn\'t receive', 'missing', 'late', 'delayed'
        ]):
            return 'problem_report'
        
        # Policy questions
        if any(phrase in message_lower for phrase in [
            'policy', 'return policy', 'shipping policy', 'how to return',
            'can i return', 'how much is shipping'
        ]):
            return 'policy_inquiry'
        
        # Product questions
        if any(phrase in message_lower for phrase in [
            'do you have', 'is it available', 'what colors', 'what sizes',
            'tell me about', 'price', 'cost'
        ]):
            return 'product_inquiry'
        
        # Help/unclear
        if any(phrase in message_lower for phrase in [
            'help', 'assist', 'support'
        ]):
            return 'general_help'
        
        # Greeting
        if any(phrase in message_lower for phrase in [
            'hello', 'hi', 'hey', 'good morning', 'good evening'
        ]):
            return 'greeting'
        
        # Thanks
        if any(phrase in message_lower for phrase in [
            'thank', 'thanks', 'appreciate'
        ]):
            return 'gratitude'
        
        # Default
        return 'unknown'
    
    def _detect_specific_question(self, message_lower: str, primary_intent: str) -> Optional[str]:
        """Detect what specifically user wants to know"""
        
        if primary_intent == 'order_status_inquiry':
            # Delivery date
            if any(phrase in message_lower for phrase in [
                'when will', 'when does', 'delivery date', 'arrive', 'get it'
            ]):
                return 'delivery_date'
            
            # Location
            if any(phrase in message_lower for phrase in [
                'where is', 'where\'s', 'kahan hai', 'location'
            ]):
                return 'current_location'
            
            # Tracking
            if any(phrase in message_lower for phrase in [
                'track', 'tracking number'
            ]):
                return 'tracking_info'
            
            # Ship date
            if any(phrase in message_lower for phrase in [
                'when was it shipped', 'ship date', 'when did it ship'
            ]):
                return 'ship_date'
            
            # Order date
            if any(phrase in message_lower for phrase in [
                'when did i order', 'when was it placed', 'order date'
            ]):
                return 'order_date'
        
        return None
    
    def _detect_missing_data(self, primary_intent: str, order_number: Optional[str], message_lower: str) -> List[str]:
        """Detect what information is missing to fulfill the request"""
        missing = []
        
        # Intents that require order number
        needs_order = [
            'order_status_inquiry',
            'order_contents_inquiry',
            'cancel_order',
            'refund_request',
            'exchange_request',
            'change_address',
            'problem_report'
        ]
        
        if primary_intent in needs_order and not order_number:
            missing.append('order_number')
        
        # Exchange needs size/color
        if primary_intent == 'exchange_request':
            if not any(word in message_lower for word in ['size', 'color', 'colour']):
                missing.append('exchange_preference')
        
        # Refund might need reason
        if primary_intent == 'refund_request':
            if not any(word in message_lower for word in ['damaged', 'wrong', 'late', 'don\'t want']):
                missing.append('reason')
        
        return missing
    
    def _detect_emotion(self, message_lower: str, conversation_history: List = None) -> str:
        """Detect user's emotional state"""
        
        # Angry/Frustrated
        if any(phrase in message_lower for phrase in [
            'ridiculous', 'unacceptable', 'terrible', 'worst', 'awful',
            'disappointed', 'frustrat', 'angry', 'pissed'
        ]):
            return 'frustrated'
        
        # Worried/Anxious
        if any(phrase in message_lower for phrase in [
            'worried', 'concerned', 'nervous', 'afraid', 'scared'
        ]):
            return 'worried'
        
        # Urgent
        if any(phrase in message_lower for phrase in [
            'urgent', 'asap', 'immediately', 'right now', 'need it tomorrow'
        ]):
            return 'urgent'
        
        # Happy/Satisfied
        if any(phrase in message_lower for phrase in [
            'love', 'great', 'amazing', 'perfect', 'excellent', 'thank'
        ]):
            return 'happy'
        
        # Confused
        if any(phrase in message_lower for phrase in [
            'confused', 'don\'t understand', 'what does', 'not clear'
        ]):
            return 'confused'
        
        # ALL CAPS = frustrated
        if any(word.isupper() and len(word) > 3 for word in message_lower.split()):
            return 'frustrated'
        
        return 'neutral'
    
    def _detect_problem_type(self, message_lower: str) -> Optional[str]:
        """Detect if user is reporting a problem"""
        
        if any(phrase in message_lower for phrase in [
            'damaged', 'broken', 'torn', 'ripped', 'defective'
        ]):
            return 'damaged_item'
        
        if any(phrase in message_lower for phrase in [
            'wrong item', 'wrong color', 'wrong size', 'different item',
            'ordered blue', 'ordered black', 'not what i ordered'
        ]):
            return 'wrong_item'
        
        if any(phrase in message_lower for phrase in [
            'not received', 'didn\'t receive', 'haven\'t received',
            'never arrived', 'missing', 'lost'
        ]):
            return 'not_received'
        
        if any(phrase in message_lower for phrase in [
            'late', 'delayed', 'overdue', 'taking too long', 'still waiting'
        ]):
            return 'delayed'
        
        return None
    
    def _should_escalate(
        self, 
        primary_intent: str, 
        problem_type: Optional[str],
        emotion: str,
        message_lower: str
    ) -> bool:
        """
        Determine if this should be escalated to human
        IMPORTANT: Escalation should be LAST RESORT, not first action
        """
        
        # User explicitly asks for human
        if any(phrase in message_lower for phrase in [
            'speak to human', 'talk to person', 'real person', 'manager',
            'escalate', 'supervisor'
        ]):
            return True
        
        # User is very frustrated (multiple indicators)
        if emotion == 'frustrated':
            frustration_words = [
                'ridiculous', 'unacceptable', 'terrible', 'worst',
                'lawsuit', 'lawyer', 'complaint'
            ]
            if sum(1 for word in frustration_words if word in message_lower) >= 2:
                return True
        
        # Critical problems that need human attention
        critical_problems = ['damaged_item', 'wrong_item', 'not_received']
        if problem_type in critical_problems:
            # But ONLY if user seems frustrated or it's been mentioned multiple times
            if emotion in ['frustrated', 'angry']:
                return True
        
        # Otherwise, try to help first!
        return False
    
    def _calculate_confidence(self, message_lower: str, primary_intent: str) -> float:
        """Calculate confidence in the intent detection"""
        
        # Very short messages are low confidence
        if len(message_lower.split()) <= 2:
            return 0.6
        
        # Clear keywords = high confidence
        if primary_intent in ['cancel_order', 'refund_request', 'exchange_request']:
            return 0.9
        
        # Unknown = low confidence
        if primary_intent == 'unknown':
            return 0.3
        
        return 0.8


# Helper function for easy use
def analyze_intent(user_message: str, context: Dict = None) -> UserIntent:
    """
    Convenience function to analyze user intent
    
    Usage:
        intent = analyze_intent("Where is my order 12345?")
        print(intent.primary_intent)  # 'order_status_inquiry'
        print(intent.specific_question)  # 'current_location'
    """
    classifier = IntentClassifier()
    return classifier.analyze(user_message, context=context or {})
