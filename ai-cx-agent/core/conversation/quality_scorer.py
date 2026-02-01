"""
Conversation Quality Scorer
Real-time quality metrics for conversation exchanges
Measures: Context retention, Empathy, Accuracy, Efficiency, Brand voice
"""

from typing import Dict, List, Optional
import re


class ConversationQualityScorer:
    """Scores conversation quality across multiple dimensions"""
    
    def __init__(self):
        """Initialize quality scorer"""
        self.score_history = []
    
    def score_exchange(self, exchange: Dict) -> Dict:
        """
        Score a single conversation exchange
        
        Args:
            exchange: {
                user_message: str,
                agent_response: str,
                emotion: str,
                scenario: str,
                context_used: bool,
                tool_results: dict,
                metadata: dict,
                brand_config: dict
            }
        
        Returns:
            {
                context_retention: float (0-10),
                empathy: float (0-10),
                accuracy: float (0-10),
                efficiency: float (0-10),
                brand_voice: float (0-10),
                overall: float (0-10),
                suggestions: list,
                grade: str (A-F)
            }
        """
        user_message = exchange.get('user_message', '')
        agent_response = exchange.get('agent_response', '')
        emotion = exchange.get('emotion', 'neutral')
        scenario = exchange.get('scenario', '')
        context_used = exchange.get('context_used', False)
        tool_results = exchange.get('tool_results', {})
        metadata = exchange.get('metadata', {})
        brand_config = exchange.get('brand_config', {})
        
        # Score each dimension
        context_score = self._score_context_retention(exchange)
        empathy_score = self._score_empathy(exchange)
        accuracy_score = self._score_accuracy(exchange)
        efficiency_score = self._score_efficiency(exchange)
        brand_voice_score = self._score_brand_voice(exchange, brand_config)
        
        # Calculate overall score (weighted average)
        overall = (
            context_score * 0.25 +      # 25% - Context is critical
            empathy_score * 0.20 +      # 20% - Customer experience
            accuracy_score * 0.25 +     # 25% - Correctness is critical
            efficiency_score * 0.15 +   # 15% - Speed matters
            brand_voice_score * 0.15    # 15% - Brand consistency
        )
        
        # Generate suggestions
        suggestions = self._generate_suggestions({
            'context_retention': context_score,
            'empathy': empathy_score,
            'accuracy': accuracy_score,
            'efficiency': efficiency_score,
            'brand_voice': brand_voice_score
        })
        
        # Assign grade
        grade = self._calculate_grade(overall)
        
        result = {
            'context_retention': round(context_score, 1),
            'empathy': round(empathy_score, 1),
            'accuracy': round(accuracy_score, 1),
            'efficiency': round(efficiency_score, 1),
            'brand_voice': round(brand_voice_score, 1),
            'overall': round(overall, 1),
            'grade': grade,
            'suggestions': suggestions
        }
        
        self.score_history.append(result)
        
        return result
    
    def _score_context_retention(self, exchange: Dict) -> float:
        """
        Score context retention (0-10)
        Did agent remember previous facts? Avoid repeat questions?
        """
        score = 10.0
        
        user_message = exchange.get('user_message', '').lower()
        agent_response = exchange.get('agent_response', '').lower()
        context_used = exchange.get('context_used', False)
        metadata = exchange.get('metadata', {})
        
        # Check if context was used when available
        if metadata.get('active_topic'):
            if context_used:
                # Bonus for using context
                score = 10.0
            else:
                # Penalty for not using available context
                score -= 3.0
        
        # Check for repeat questions (sign of poor context)
        repeat_indicators = [
            'which order',
            'what order',
            'order number',
            'can you provide',
            'could you tell me',
            'what is your'
        ]
        
        if any(indicator in agent_response for indicator in repeat_indicators):
            # Check if this info was already provided
            if context_used:
                # Asked for info that should be in context
                score -= 4.0
        
        # Check if agent acknowledged context
        context_acknowledgments = [
            'your order',
            'as mentioned',
            'as we discussed',
            'continuing from'
        ]
        
        if context_used and any(ack in agent_response for ack in context_acknowledgments):
            score += 1.0
        
        return max(0.0, min(10.0, score))
    
    def _score_empathy(self, exchange: Dict) -> float:
        """
        Score empathy (0-10)
        Was emotion detected and addressed appropriately?
        """
        score = 7.0  # Start neutral
        
        emotion = exchange.get('emotion', 'neutral')
        agent_response = exchange.get('agent_response', '').lower()
        metadata = exchange.get('metadata', {})
        
        # High empathy phrases
        empathy_phrases = [
            'i understand',
            'i completely understand',
            'i appreciate',
            'i apologize',
            "i'm sorry",
            'that must be',
            'i can see',
            'frustrating',
            'concerning'
        ]
        
        # Check if emotion requires empathy
        needs_empathy = emotion in ['frustrated', 'confused', 'urgent']
        
        if needs_empathy:
            # Check if empathy was shown
            empathy_shown = any(phrase in agent_response for phrase in empathy_phrases)
            
            if empathy_shown:
                score = 10.0  # Excellent empathy
            else:
                score = 4.0   # Missed empathy opportunity
        else:
            # Neutral or positive emotion
            if any(phrase in agent_response for phrase in empathy_phrases):
                score = 9.0  # Good empathy even when not critical
            else:
                score = 7.0  # Neutral (acceptable)
        
        # Check for escalation with empathy
        if metadata.get('escalation'):
            if any(phrase in agent_response for phrase in empathy_phrases):
                score = 10.0  # Great empathy before escalation
            else:
                score -= 2.0  # Should show empathy when escalating
        
        return max(0.0, min(10.0, score))
    
    def _score_accuracy(self, exchange: Dict) -> float:
        """
        Score accuracy (0-10)
        Were facts correct? No hallucinations?
        """
        score = 10.0  # Start assuming accurate
        
        agent_response = exchange.get('agent_response', '').lower()
        tool_results = exchange.get('tool_results', {})
        metadata = exchange.get('metadata', {})
        
        # Check if tool was used when needed
        tool_used = metadata.get('tool_used')
        tool_success = metadata.get('tool_success', False)
        
        if tool_used:
            if tool_success:
                # Tool provided data - good!
                score = 10.0
                
                # Check if response likely used tool data
                # (This is heuristic - full check would need LLM)
                if len(agent_response) > 50:
                    score = 10.0  # Substantial response with tool data
            else:
                # Tool failed - check if handled gracefully
                if 'unable' in agent_response or 'trouble' in agent_response:
                    score = 8.0  # Honest about limitation
                else:
                    score = 6.0  # Tool failed, response might be inaccurate
        
        # Check for hallucination indicators (vague/uncertain language)
        vague_phrases = [
            'might be',
            'could be',
            'possibly',
            'i think',
            'maybe'
        ]
        
        vague_count = sum(1 for phrase in vague_phrases if phrase in agent_response)
        if vague_count > 2:
            score -= 2.0  # Too much uncertainty
        
        # Check for specific facts (dates, numbers, IDs)
        has_specifics = bool(re.search(r'\d+', agent_response))
        
        if tool_success and has_specifics:
            score = 10.0  # Specific data from tool
        elif tool_success and not has_specifics:
            score -= 1.0  # Had data but didn't use specifics
        
        return max(0.0, min(10.0, score))
    
    def _score_efficiency(self, exchange: Dict) -> float:
        """
        Score efficiency (0-10)
        Was user's need met quickly and directly?
        """
        score = 8.0  # Start neutral
        
        user_message = exchange.get('user_message', '').lower()
        agent_response = exchange.get('agent_response', '').lower()
        metadata = exchange.get('metadata', {})
        
        # Check response length (should be appropriate)
        response_length = len(agent_response)
        
        if response_length < 30:
            score = 5.0  # Too short, likely unhelpful
        elif 30 <= response_length <= 300:
            score = 10.0  # Good length
        elif 300 < response_length <= 500:
            score = 8.0  # Bit long but ok
        else:
            score = 6.0  # Too long, inefficient
        
        # Check if question was answered directly
        question_words = ['where', 'when', 'why', 'how', 'what', 'who']
        is_question = any(word in user_message for word in question_words)
        
        if is_question:
            # Should have direct answer in first 100 chars
            first_part = agent_response[:100]
            
            # Check for direct answer indicators
            direct_answer = any(word in first_part for word in ['is', 'are', 'will', 'can', 'yes', 'no'])
            
            if direct_answer:
                score += 2.0  # Direct answer
            else:
                score -= 1.0  # Indirect answer
        
        # Penalize if asks for info already provided
        clarification_requests = [
            'could you provide',
            'can you tell me',
            'which order',
            'what is'
        ]
        
        if any(req in agent_response for req in clarification_requests):
            # Asking for info might be inefficient
            if not metadata.get('context_used'):
                score -= 2.0  # Asked for context that wasn't used
        
        return max(0.0, min(10.0, score))
    
    def _score_brand_voice(self, exchange: Dict, brand_config: Dict) -> float:
        """
        Score brand voice adherence (0-10)
        Did response match brand personality?
        """
        score = 7.0  # Start neutral
        
        agent_response = exchange.get('agent_response', '')
        voice_config = brand_config.get('voice', {})
        
        if not voice_config:
            return 7.0  # No voice config, can't judge
        
        # Check emoji usage
        emoji_usage = voice_config.get('emoji_usage', 'moderate')
        has_emoji = any(ord(c) > 127 for c in agent_response)
        
        if emoji_usage == 'none':
            if has_emoji:
                score -= 3.0  # Used emoji when shouldn't
            else:
                score += 1.0  # Correctly avoided emoji
        elif emoji_usage in ['moderate', 'frequent']:
            if has_emoji:
                score += 1.0  # Good emoji usage
            else:
                score -= 1.0  # Should use emoji
        
        # Check signature phrases
        signature_phrases = voice_config.get('signature_phrases', [])
        used_signature = any(
            phrase.lower() in agent_response.lower() 
            for phrase in signature_phrases
        )
        
        if used_signature:
            score += 2.0  # Used brand phrases
        
        # Check forbidden phrases
        forbidden_phrases = voice_config.get('forbidden_phrases', [])
        used_forbidden = any(
            phrase.lower() in agent_response.lower() 
            for phrase in forbidden_phrases
        )
        
        if used_forbidden:
            score -= 3.0  # Used forbidden phrases
        
        # Check tone (heuristic based on word choice)
        tone = voice_config.get('tone', '')
        
        if 'friendly' in tone or 'casual' in tone:
            casual_markers = ['hey', 'hi there', '!', 'great', 'awesome']
            if any(marker in agent_response.lower() for marker in casual_markers):
                score += 1.0
        
        if 'professional' in tone or 'formal' in tone:
            formal_markers = ['regarding', 'please', 'kindly', 'assist']
            if any(marker in agent_response.lower() for marker in formal_markers):
                score += 1.0
        
        return max(0.0, min(10.0, score))
    
    def _generate_suggestions(self, scores: Dict) -> List[str]:
        """
        Generate improvement suggestions based on scores
        
        Args:
            scores: Dict of dimension scores
        
        Returns:
            List of actionable suggestions
        """
        suggestions = []
        
        if scores['context_retention'] < 7.0:
            suggestions.append("Improve context retention: Use active topic information to avoid repeat questions")
        
        if scores['empathy'] < 7.0:
            suggestions.append("Increase empathy: Acknowledge customer emotions before providing solutions")
        
        if scores['accuracy'] < 7.0:
            suggestions.append("Enhance accuracy: Use tool results more explicitly in responses")
        
        if scores['efficiency'] < 7.0:
            suggestions.append("Boost efficiency: Provide direct answers earlier in response")
        
        if scores['brand_voice'] < 7.0:
            suggestions.append("Align with brand voice: Check emoji usage and signature phrases")
        
        # Positive reinforcement
        if all(score >= 8.0 for score in scores.values()):
            suggestions.append("Excellent! All quality metrics are strong")
        
        return suggestions
    
    def _calculate_grade(self, overall_score: float) -> str:
        """Convert score to letter grade"""
        if overall_score >= 9.0:
            return 'A+'
        elif overall_score >= 8.5:
            return 'A'
        elif overall_score >= 8.0:
            return 'A-'
        elif overall_score >= 7.5:
            return 'B+'
        elif overall_score >= 7.0:
            return 'B'
        elif overall_score >= 6.5:
            return 'B-'
        elif overall_score >= 6.0:
            return 'C+'
        elif overall_score >= 5.5:
            return 'C'
        elif overall_score >= 5.0:
            return 'C-'
        elif overall_score >= 4.0:
            return 'D'
        else:
            return 'F'
    
    def get_average_scores(self) -> Dict:
        """Get average scores across all exchanges"""
        if not self.score_history:
            return {
                'context_retention': 0.0,
                'empathy': 0.0,
                'accuracy': 0.0,
                'efficiency': 0.0,
                'brand_voice': 0.0,
                'overall': 0.0
            }
        
        totals = {
            'context_retention': 0.0,
            'empathy': 0.0,
            'accuracy': 0.0,
            'efficiency': 0.0,
            'brand_voice': 0.0,
            'overall': 0.0
        }
        
        for score in self.score_history:
            for key in totals:
                totals[key] += score[key]
        
        count = len(self.score_history)
        
        return {
            key: round(value / count, 1) 
            for key, value in totals.items()
        }
    
    def __repr__(self) -> str:
        avg = self.get_average_scores()
        return f"QualityScorer(avg_overall={avg['overall']}, exchanges={len(self.score_history)})"


# Testing function
def test_quality_scorer():
    """Test quality scorer"""
    print("🧪 TESTING QUALITY SCORER")
    print("=" * 70)
    print()
    
    scorer = ConversationQualityScorer()
    
    # Test case 1: Good exchange
    print("TEST 1: High-quality exchange")
    exchange1 = {
        'user_message': "Where's my order 12345?",
        'agent_response': "Your order 12345 is currently being shipped and will arrive by February 5th. You can track it here: track.example.com/12345",
        'emotion': 'neutral',
        'scenario': 'order_status',
        'context_used': True,
        'tool_results': {'success': True},
        'metadata': {'tool_used': 'get_order_status', 'tool_success': True, 'active_topic': {'type': 'ORDER'}},
        'brand_config': {'voice': {'emoji_usage': 'moderate', 'signature_phrases': []}}
    }
    
    score1 = scorer.score_exchange(exchange1)
    print(f"Overall Score: {score1['overall']}/10 ({score1['grade']})")
    print(f"  Context: {score1['context_retention']}/10")
    print(f"  Empathy: {score1['empathy']}/10")
    print(f"  Accuracy: {score1['accuracy']}/10")
    print(f"  Efficiency: {score1['efficiency']}/10")
    print(f"  Brand Voice: {score1['brand_voice']}/10")
    if score1['suggestions']:
        print(f"  Suggestions: {', '.join(score1['suggestions'])}")
    print()
    
    # Test case 2: Poor empathy
    print("TEST 2: Needs more empathy")
    exchange2 = {
        'user_message': "My order is late! This is terrible!",
        'agent_response': "Your order will arrive in 3 days.",
        'emotion': 'frustrated',
        'scenario': 'delay',
        'context_used': True,
        'tool_results': {'success': True},
        'metadata': {'tool_used': 'get_order_status', 'tool_success': True},
        'brand_config': {'voice': {'emoji_usage': 'none'}}
    }
    
    score2 = scorer.score_exchange(exchange2)
    print(f"Overall Score: {score2['overall']}/10 ({score2['grade']})")
    print(f"  Context: {score2['context_retention']}/10")
    print(f"  Empathy: {score2['empathy']}/10")
    print(f"  Accuracy: {score2['accuracy']}/10")
    print(f"  Efficiency: {score2['efficiency']}/10")
    print(f"  Brand Voice: {score2['brand_voice']}/10")
    if score2['suggestions']:
        print(f"  Suggestions:")
        for s in score2['suggestions']:
            print(f"    - {s}")
    print()
    
    # Average scores
    print("=" * 70)
    avg = scorer.get_average_scores()
    print(f"Average Scores Across {len(scorer.score_history)} Exchanges:")
    print(f"  Overall: {avg['overall']}/10")
    print(f"  Context: {avg['context_retention']}/10")
    print(f"  Empathy: {avg['empathy']}/10")
    print(f"  Accuracy: {avg['accuracy']}/10")
    print()
    
    print("🎉 Quality scorer tests complete!")


if __name__ == "__main__":
    test_quality_scorer()
