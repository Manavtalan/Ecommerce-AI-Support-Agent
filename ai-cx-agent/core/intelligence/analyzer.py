"""
Intelligence Analyzer
Analyzes data to answer complex questions like "why is it late?"
"""

from typing import Dict, Optional
from datetime import datetime, timedelta


class IntelligenceAnalyzer:
    """Analyzes data to provide intelligent answers"""
    
    @staticmethod
    def analyze_order_delay(order_data: Dict, user_question: str) -> Optional[Dict]:
        """
        Analyze if order is actually late and why
        
        Returns:
            {
                'is_late': bool,
                'days_late': int,
                'reason': str,
                'explanation': str
            }
        """
        if not order_data or not order_data.get('success'):
            return None
        
        shipping = order_data.get('shipping', {})
        estimated_delivery = shipping.get('estimated_delivery')
        
        if not estimated_delivery:
            return None
        
        # Parse estimated delivery date
        try:
            # Handle different date formats
            if 'T' in estimated_delivery:
                estimated_date = datetime.fromisoformat(estimated_delivery.replace('Z', '+00:00'))
            else:
                estimated_date = datetime.strptime(estimated_delivery, '%Y-%m-%d')
            
            today = datetime.now()
            
            # Calculate if late
            is_late = today.date() > estimated_date.date()
            days_difference = (today.date() - estimated_date.date()).days
            
            if is_late:
                return {
                    'is_late': True,
                    'days_late': days_difference,
                    'reason': 'delivery_overdue',
                    'explanation': f"Your order was expected on {estimated_delivery} but it's now {days_difference} day(s) overdue. Current status: {shipping.get('last_update', 'Unknown')}"
                }
            else:
                # Not late
                days_until_delivery = (estimated_date.date() - today.date()).days
                
                if days_until_delivery == 0:
                    timing = "today"
                elif days_until_delivery == 1:
                    timing = "tomorrow"
                else:
                    timing = f"in {days_until_delivery} days"
                
                return {
                    'is_late': False,
                    'days_late': 0,
                    'reason': 'on_track',
                    'explanation': f"Actually, your order is NOT late! It's expected to arrive {timing} ({estimated_delivery}). Current status: {shipping.get('last_update', 'In transit')}. It's right on schedule! 📦"
                }
        
        except Exception as e:
            print(f"Error analyzing delivery: {e}")
            return None
    
    @staticmethod
    def analyze_question_intent(user_message: str, order_data: Dict) -> Dict:
        """
        Analyze what the user is actually asking
        
        Returns analysis with recommended response approach
        """
        message_lower = user_message.lower()
        
        analysis = {
            'question_type': 'general',
            'needs_analysis': False,
            'special_instructions': None
        }
        
        # Check if asking about delay/lateness
        delay_keywords = ['late', 'delay', 'slow', 'taking long', 'not arrived', 'overdue']
        if any(keyword in message_lower for keyword in delay_keywords):
            analysis['question_type'] = 'delay_inquiry'
            analysis['needs_analysis'] = True
            
            # Analyze if actually late
            delay_analysis = IntelligenceAnalyzer.analyze_order_delay(order_data, user_message)
            
            if delay_analysis:
                analysis['delay_analysis'] = delay_analysis
                
                if delay_analysis['is_late']:
                    analysis['special_instructions'] = f"IMPORTANT: Order IS late by {delay_analysis['days_late']} days. Apologize and explain: {delay_analysis['explanation']}"
                else:
                    analysis['special_instructions'] = f"IMPORTANT: Order is NOT late! Reassure customer: {delay_analysis['explanation']}"
        
        # Check if asking what's in order
        content_keywords = ['what is', 'what\'s in', 'contains', 'what did i order', 'what am i getting']
        if any(keyword in message_lower for keyword in content_keywords):
            analysis['question_type'] = 'order_contents'
            analysis['special_instructions'] = "IMPORTANT: Customer wants to know WHAT'S IN THE ORDER. List all items with details (name, color, size, quantity)."
        
        # Check if asking about location
        location_keywords = ['where is', 'location', 'current status', 'track']
        if any(keyword in message_lower for keyword in location_keywords):
            analysis['question_type'] = 'location_inquiry'
            analysis['special_instructions'] = "IMPORTANT: Customer wants current LOCATION. Tell them exactly where the package is now and when it will arrive."
        
        return analysis


# Test function
def test_analyzer():
    """Test the intelligence analyzer"""
    print("🧪 TESTING INTELLIGENCE ANALYZER")
    print("=" * 70)
    
    # Mock order data
    order_data = {
        'success': True,
        'order_id': '12345',
        'shipping': {
            'estimated_delivery': '2026-01-29',
            'last_update': 'Out for delivery',
            'current_location': 'Bangalore Local Office'
        }
    }
    
    # Test 1: "Why is it late?" when NOT late
    print("\nTEST 1: 'Why is it late?' (when not actually late)")
    analysis = IntelligenceAnalyzer.analyze_question_intent("Why is it late?", order_data)
    print(f"Question Type: {analysis['question_type']}")
    print(f"Needs Analysis: {analysis['needs_analysis']}")
    if analysis.get('delay_analysis'):
        print(f"Is Late: {analysis['delay_analysis']['is_late']}")
        print(f"Explanation: {analysis['delay_analysis']['explanation']}")
    print(f"Special Instructions: {analysis.get('special_instructions', 'None')[:100]}...")
    
    # Test 2: "What's in my order?"
    print("\nTEST 2: 'What's in my order?'")
    analysis = IntelligenceAnalyzer.analyze_question_intent("What's in my order?", order_data)
    print(f"Question Type: {analysis['question_type']}")
    print(f"Special Instructions: {analysis.get('special_instructions', 'None')}")
    
    # Test 3: "Where is my order?"
    print("\nTEST 3: 'Where is my order?'")
    analysis = IntelligenceAnalyzer.analyze_question_intent("Where is my order?", order_data)
    print(f"Question Type: {analysis['question_type']}")
    print(f"Special Instructions: {analysis.get('special_instructions', 'None')}")
    
    print("\n" + "=" * 70)
    print("✅ Intelligence analyzer tests complete!")


if __name__ == "__main__":
    test_analyzer()
