"""
Escalation Manager
Smart escalation system with tier-based triggers
Prevents unnecessary escalations while catching critical issues
"""

from typing import Dict, List, Optional
import re
from datetime import datetime


class EscalationManager:
    """Manages conversation escalation with intelligent triggers"""
    
    # Tier 1: MANDATORY escalation (immediate)
    TIER1_KEYWORDS = [
        # Refunds & cancellations
        "refund", "money back", "cancel order", "cancel my order",
        # Legal threats
        "lawyer", "legal action", "sue", "court", "attorney",
        # Chargebacks & fraud
        "chargeback", "dispute charge", "fraud", "scam", "stolen",
        # Severe abuse
        "fuck", "shit", "bastard", "bitch",
        # Regulatory
        "consumer court", "consumer forum", "file complaint"
    ]
    
    # Tier 2: CONDITIONAL escalation
    TIER2_KEYWORDS = [
        # Explicit human request
        "speak to human", "talk to person", "real person", 
        "customer service", "manager", "supervisor",
        # Strong frustration
        "ridiculous", "unacceptable", "disgusting", "horrible",
        "worst", "terrible", "pathetic", "useless"
    ]
    
    # Escalation prevention keywords (show empathy first)
    EMPATHY_TRIGGERS = [
        "frustrated", "upset", "angry", "disappointed",
        "unhappy", "dissatisfied", "concerned"
    ]
    
    def __init__(self):
        """Initialize escalation manager"""
        self.escalation_history = []
    
    def should_escalate(self, context: Dict) -> Dict:
        """
        Determine if conversation should escalate
        
        Args:
            context: {
                message: str,
                emotion: str,
                emotion_history: list,
                confidence: float,
                scenario: str,
                tool_failures: int
            }
        
        Returns:
            {
                should_escalate: bool,
                escalation_tier: int (1-3),
                reason: str,
                urgency: str (low/medium/high/critical),
                suggested_message: str,
                prevent_escalation: bool
            }
        """
        message = context.get('message', '').lower()
        emotion = context.get('emotion', 'neutral')
        emotion_history = context.get('emotion_history', [])
        confidence = context.get('confidence', 1.0)
        scenario = context.get('scenario', '')
        tool_failures = context.get('tool_failures', 0)
        
        # Check Tier 1: Mandatory escalation
        tier1_result = self._check_tier1_mandatory(message)
        if tier1_result['escalate']:
            return {
                'should_escalate': True,
                'escalation_tier': 1,
                'reason': tier1_result['reason'],
                'urgency': 'critical',
                'suggested_message': self._build_escalation_message(
                    tier1_result['reason'], 
                    'critical'
                ),
                'prevent_escalation': False,
                'keywords_matched': tier1_result['keywords']
            }
        
        # Check Tier 2: Conditional escalation
        tier2_result = self._check_tier2_conditional(
            message, 
            emotion, 
            emotion_history,
            confidence,
            tool_failures
        )
        if tier2_result['escalate']:
            # Check if we should try empathy first (Tier 3)
            if self._should_try_empathy_first(emotion_history):
                return {
                    'should_escalate': False,
                    'escalation_tier': 3,
                    'reason': 'empathy_first',
                    'urgency': 'medium',
                    'suggested_message': self._build_empathy_message(emotion),
                    'prevent_escalation': True,
                    'note': 'Try empathy before escalating'
                }
            
            return {
                'should_escalate': True,
                'escalation_tier': 2,
                'reason': tier2_result['reason'],
                'urgency': tier2_result['urgency'],
                'suggested_message': self._build_escalation_message(
                    tier2_result['reason'],
                    tier2_result['urgency']
                ),
                'prevent_escalation': False,
                'keywords_matched': tier2_result.get('keywords', [])
            }
        
        # No escalation needed
        return {
            'should_escalate': False,
            'escalation_tier': 0,
            'reason': 'none',
            'urgency': 'none',
            'suggested_message': None,
            'prevent_escalation': False
        }
    
    def _check_tier1_mandatory(self, message: str) -> Dict:
        """
        Check Tier 1: Mandatory escalation triggers
        
        Returns:
            {escalate: bool, reason: str, keywords: list}
        """
        matched_keywords = []
        
        for keyword in self.TIER1_KEYWORDS:
            if keyword in message:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            # Determine specific reason
            if any(k in matched_keywords for k in ["refund", "money back"]):
                reason = "refund_request"
            elif any(k in matched_keywords for k in ["cancel order", "cancel my order"]):
                reason = "cancellation_request"
            elif any(k in matched_keywords for k in ["lawyer", "legal", "sue", "court"]):
                reason = "legal_threat"
            elif any(k in matched_keywords for k in ["chargeback", "dispute", "fraud", "scam"]):
                reason = "chargeback_fraud"
            elif any(k in matched_keywords for k in ["fuck", "shit", "bastard", "bitch"]):
                reason = "severe_abuse"
            else:
                reason = "tier1_trigger"
            
            return {
                'escalate': True,
                'reason': reason,
                'keywords': matched_keywords
            }
        
        return {'escalate': False, 'reason': None, 'keywords': []}
    
    def _check_tier2_conditional(
        self,
        message: str,
        emotion: str,
        emotion_history: List[Dict],
        confidence: float,
        tool_failures: int
    ) -> Dict:
        """
        Check Tier 2: Conditional escalation triggers
        
        Returns:
            {escalate: bool, reason: str, urgency: str, keywords: list}
        """
        matched_keywords = []
        
        # Check for explicit human request
        for keyword in self.TIER2_KEYWORDS[:4]:  # Human request keywords
            if keyword in message:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            return {
                'escalate': True,
                'reason': 'explicit_human_request',
                'urgency': 'high',
                'keywords': matched_keywords
            }
        
        # Check for repeated frustration (3+ frustrated messages)
        if len(emotion_history) >= 3:
            recent_emotions = [e.get('emotion') for e in emotion_history[-3:]]
            frustrated_count = sum(1 for e in recent_emotions if e == 'frustrated')
            
            if frustrated_count >= 3:
                return {
                    'escalate': True,
                    'reason': 'repeated_frustration',
                    'urgency': 'high',
                    'keywords': ['repeated frustration']
                }
        
        # Check for low confidence responses
        if confidence < 0.6:
            return {
                'escalate': True,
                'reason': 'low_confidence',
                'urgency': 'medium',
                'keywords': ['low confidence']
            }
        
        # Check for multiple tool failures
        if tool_failures >= 2:
            return {
                'escalate': True,
                'reason': 'tool_failures',
                'urgency': 'medium',
                'keywords': ['system issues']
            }
        
        # Check for strong frustration keywords
        for keyword in self.TIER2_KEYWORDS[4:]:  # Frustration keywords
            if keyword in message:
                matched_keywords.append(keyword)
        
        if len(matched_keywords) >= 2:  # Multiple strong frustration words
            return {
                'escalate': True,
                'reason': 'extreme_frustration',
                'urgency': 'high',
                'keywords': matched_keywords
            }
        
        return {'escalate': False, 'reason': None, 'urgency': None, 'keywords': []}
    
    def _should_try_empathy_first(self, emotion_history: List[Dict]) -> bool:
        """
        Determine if we should try empathy before escalating
        
        Args:
            emotion_history: List of emotion records
        
        Returns:
            True if this is first frustration (try empathy first)
        """
        if len(emotion_history) < 2:
            return True  # First frustration, try empathy
        
        # If already tried empathy (previous frustration), escalate
        recent_frustrated = sum(
            1 for e in emotion_history[-2:] 
            if e.get('emotion') == 'frustrated'
        )
        
        return recent_frustrated < 2
    
    def _build_escalation_message(self, reason: str, urgency: str) -> str:
        """
        Build appropriate escalation message
        
        Args:
            reason: Escalation reason
            urgency: Urgency level
        
        Returns:
            Suggested escalation message
        """
        messages = {
            'refund_request': "I understand you'd like a refund. Let me connect you with our support team who can help process that for you right away.",
            
            'cancellation_request': "I understand you need to cancel your order. Let me connect you with our team who can assist with that immediately.",
            
            'legal_threat': "I understand your concerns. Let me connect you with our customer relations team who can address this matter properly.",
            
            'chargeback_fraud': "I take your concerns very seriously. Let me connect you with our support team immediately to resolve this.",
            
            'severe_abuse': "I'm here to help, but I need us to communicate respectfully. Let me connect you with a team member who can assist you.",
            
            'explicit_human_request': "Of course! Let me connect you with a team member right away.",
            
            'repeated_frustration': "I can see this has been frustrating for you, and I apologize for that. Let me connect you with our support team who can give this the attention it deserves.",
            
            'low_confidence': "I want to make sure you get accurate information. Let me connect you with a specialist who can help you better.",
            
            'tool_failures': "I'm having trouble accessing our systems right now. Let me connect you with our support team who can assist you directly.",
            
            'extreme_frustration': "I completely understand your frustration, and I apologize for the inconvenience. Let me connect you with our support team who can resolve this for you."
        }
        
        return messages.get(reason, "Let me connect you with our support team who can assist you better.")
    
    def _build_empathy_message(self, emotion: str) -> str:
        """
        Build empathy-first message (Tier 3 prevention)
        
        Args:
            emotion: Detected emotion
        
        Returns:
            Empathy message
        """
        if emotion == 'frustrated':
            return "I completely understand your frustration, and I'm truly sorry for the inconvenience. Let me do everything I can to help resolve this for you."
        elif emotion == 'urgent':
            return "I understand this is urgent for you. Let me prioritize this and get you the information you need right away."
        else:
            return "I understand this is important to you. Let me help resolve this for you."
    
    def log_escalation(self, escalation: Dict):
        """Log escalation for tracking"""
        escalation['timestamp'] = datetime.now().isoformat()
        self.escalation_history.append(escalation)
    
    def get_escalation_stats(self) -> Dict:
        """Get escalation statistics"""
        if not self.escalation_history:
            return {
                'total_escalations': 0,
                'by_tier': {},
                'by_reason': {},
                'prevented': 0
            }
        
        total = len(self.escalation_history)
        by_tier = {}
        by_reason = {}
        prevented = 0
        
        for esc in self.escalation_history:
            tier = esc.get('escalation_tier', 0)
            reason = esc.get('reason', 'unknown')
            
            by_tier[tier] = by_tier.get(tier, 0) + 1
            by_reason[reason] = by_reason.get(reason, 0) + 1
            
            if esc.get('prevent_escalation'):
                prevented += 1
        
        return {
            'total_escalations': total,
            'by_tier': by_tier,
            'by_reason': by_reason,
            'prevented': prevented,
            'prevention_rate': (prevented / total * 100) if total > 0 else 0
        }
    
    def __repr__(self) -> str:
        stats = self.get_escalation_stats()
        return f"EscalationManager(escalations={stats['total_escalations']}, prevented={stats['prevented']})"


# Testing function
def test_escalation_manager():
    """Test escalation manager"""
    print("🧪 TESTING ESCALATION MANAGER")
    print("=" * 70)
    print()
    
    manager = EscalationManager()
    
    test_cases = [
        # Tier 1: Mandatory
        {
            'name': 'Refund Request',
            'context': {
                'message': 'I want a refund immediately',
                'emotion': 'frustrated'
            },
            'expected_tier': 1
        },
        {
            'name': 'Legal Threat',
            'context': {
                'message': 'I will take legal action',
                'emotion': 'frustrated'
            },
            'expected_tier': 1
        },
        
        # Tier 2: Conditional
        {
            'name': 'Human Request',
            'context': {
                'message': 'I want to speak to a human',
                'emotion': 'neutral'
            },
            'expected_tier': 2
        },
        {
            'name': 'Repeated Frustration',
            'context': {
                'message': 'This is still not resolved',
                'emotion': 'frustrated',
                'emotion_history': [
                    {'emotion': 'frustrated'},
                    {'emotion': 'frustrated'},
                    {'emotion': 'frustrated'}
                ]
            },
            'expected_tier': 2
        },
        
        # No escalation
        {
            'name': 'Normal Query',
            'context': {
                'message': 'Where is my order?',
                'emotion': 'neutral'
            },
            'expected_tier': 0
        },
    ]
    
    for test in test_cases:
        result = manager.should_escalate(test['context'])
        
        tier = result['escalation_tier']
        expected = test['expected_tier']
        
        icon = "✅" if tier == expected else "❌"
        
        print(f"{icon} {test['name']}")
        print(f"   Message: '{test['context']['message']}'")
        print(f"   Expected Tier: {expected}, Got: {tier}")
        print(f"   Should Escalate: {result['should_escalate']}")
        print(f"   Reason: {result['reason']}")
        print(f"   Urgency: {result['urgency']}")
        if result.get('suggested_message'):
            print(f"   Message: {result['suggested_message'][:80]}...")
        print()
    
    print("🎉 Escalation manager tests complete!")


if __name__ == "__main__":
    test_escalation_manager()
