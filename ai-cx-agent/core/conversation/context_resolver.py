"""
Context Resolver
LLM-powered intelligent context resolution
Replaces keyword-based follow-up detection
"""

import json
from typing import Dict, Optional
from openai import OpenAI


class ContextResolver:
    """Resolves whether user message relates to active conversation topic"""
    
    def __init__(self, llm_client: OpenAI, model: str = "gpt-4o-mini"):
        """
        Initialize context resolver
        
        Args:
            llm_client: OpenAI client instance
            model: Model to use for context resolution
        """
        self.client = llm_client
        self.model = model
    
    def resolve_context(
        self,
        current_message: str,
        active_topic: Dict
    ) -> Dict:
        """
        Determine if message relates to current topic
        
        Args:
            current_message: User's current message
            active_topic: {
                topic_type: str (ORDER, POLICY, PRODUCT, etc.),
                entity_id: str (order_id, etc.),
                context: str (optional description)
            }
        
        Returns:
            {
                about_current_topic: bool,
                confidence: float (0-1),
                ambiguous: bool,
                suggested_action: str
            }
        """
        if not active_topic:
            return {
                'about_current_topic': False,
                'confidence': 0.0,
                'ambiguous': False,
                'suggested_action': 'new_topic'
            }
        
        # Build prompt for LLM
        prompt = self._build_context_prompt(current_message, active_topic)
        
        try:
            # Call LLM for context resolution
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a context resolution assistant. Analyze if user messages relate to the current conversation topic. Respond ONLY with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=150
            )
            
            # Parse LLM response
            llm_text = response.choices[0].message.content.strip()
            result = self._parse_llm_response(llm_text)
            
            return result
        
        except Exception as e:
            print(f"⚠️  Context resolution failed: {e}")
            # Fallback: assume it's about current topic with low confidence
            return {
                'about_current_topic': True,
                'confidence': 0.5,
                'ambiguous': True,
                'suggested_action': 'clarify'
            }
    
    def _build_context_prompt(self, message: str, topic: Dict) -> str:
        """
        Build prompt for LLM context resolution
        
        Args:
            message: Current user message
            topic: Active topic details
        
        Returns:
            Formatted prompt
        """
        topic_type = topic.get('topic_type', 'unknown')
        entity_id = topic.get('entity_id', 'N/A')
        context = topic.get('context', '')
        
        prompt = f"""Current conversation topic:
- Type: {topic_type}
- Entity: {entity_id}
- Context: {context if context else 'No additional context'}

User's new message: "{message}"

Question: Is this new message about the current topic?

Analyze:
1. Does the message reference the current topic explicitly or implicitly?
2. Are pronouns like "it", "that", "this" referring to the current topic?
3. Are questions like "why?", "when?", "where?" asking about the current topic?
4. Or is this a completely new question/topic?

Respond with ONLY a JSON object:
{{
    "about_current_topic": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "ambiguous": true/false,
    "suggested_action": "continue/new_topic/clarify"
}}

Examples:
- If current topic is "Order 12345" and message is "why late?" → about_current_topic: true
- If current topic is "Order 12345" and message is "what's your return policy?" → about_current_topic: false
- If message is "it" or "that" → about_current_topic: true (pronoun reference)
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict:
        """
        Parse LLM response into structured format
        
        Args:
            response: Raw LLM response text
        
        Returns:
            Parsed result dict
        """
        try:
            # Try to extract JSON from response
            # Handle cases where LLM adds markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            parsed = json.loads(response)
            
            # Ensure required fields
            return {
                'about_current_topic': parsed.get('about_current_topic', False),
                'confidence': float(parsed.get('confidence', 0.5)),
                'ambiguous': parsed.get('ambiguous', False),
                'suggested_action': parsed.get('suggested_action', 'clarify'),
                'reasoning': parsed.get('reasoning', '')
            }
        
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse LLM response: {e}")
            print(f"   Response was: {response}")
            
            # Fallback parsing - look for keywords
            response_lower = response.lower()
            
            about_topic = any(word in response_lower for word in ['yes', 'true', 'about', 'related'])
            
            return {
                'about_current_topic': about_topic,
                'confidence': 0.6,
                'ambiguous': True,
                'suggested_action': 'clarify',
                'reasoning': 'Fallback parsing'
            }
    
    def __repr__(self) -> str:
        return f"ContextResolver(model={self.model})"


# Convenience function for testing
def test_context_resolution():
    """Quick test of context resolver"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resolver = ContextResolver(client)
    
    # Test topic
    topic = {
        'topic_type': 'ORDER',
        'entity_id': '12345',
        'context': 'User asked about order status'
    }
    
    # Test messages
    test_cases = [
        "why is it late?",
        "where is it?",
        "eta?",
        "what's your return policy?",
        "can I cancel that?",
        "tell me about shipping"
    ]
    
    print("🧪 Testing Context Resolution")
    print("=" * 70)
    print(f"Active topic: {topic['topic_type']} - {topic['entity_id']}")
    print()
    
    for message in test_cases:
        result = resolver.resolve_context(message, topic)
        
        icon = "✅" if result['about_current_topic'] else "🔄"
        print(f"{icon} '{message}'")
        print(f"   About topic: {result['about_current_topic']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Action: {result['suggested_action']}")
        if result.get('reasoning'):
            print(f"   Reasoning: {result['reasoning']}")
        print()


if __name__ == "__main__":
    test_context_resolution()
