"""
LLM Response Composer - WITH RETRY LOGIC
Generates contextual responses with exponential backoff
"""

from typing import Dict, List, Optional
from openai import OpenAI
import os
import time
from dotenv import load_dotenv

load_dotenv()


class LLMResponseComposer:
    """Composes LLM responses with intelligent retry logic"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize composer with retry capability"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.retry_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'retries': 0
        }
    
    def compose_response(
        self,
        scenario: str,
        facts: Dict,
        constraints: List[str],
        emotion: str = "neutral",
        brand_voice: Optional[Dict] = None,
        system_prompt: Optional[str] = None,
        max_retries: int = 2
    ) -> str:
        """
        Compose response with retry logic and exponential backoff
        
        Args:
            scenario: Type of scenario
            facts: Context and facts
            constraints: Response constraints
            emotion: Detected emotion
            brand_voice: Brand voice configuration
            system_prompt: Custom system prompt
            max_retries: Maximum retry attempts (default: 2)
        
        Returns:
            Generated response string
        """
        self.retry_stats['total_calls'] += 1
        
        retries = 0
        backoff = 1.0  # Start with 1 second
        
        while retries <= max_retries:
            try:
                # Build prompt
                user_prompt = self._build_prompt(scenario, facts, constraints, emotion)
                
                # Use custom system prompt or build default
                if system_prompt:
                    sys_prompt = system_prompt
                else:
                    sys_prompt = self._build_system_prompt(brand_voice, constraints)
                
                # Call LLM
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                # Success!
                self.retry_stats['successful_calls'] += 1
                if retries > 0:
                    print(f"   ✅ Retry successful after {retries} attempt(s)")
                
                return response.choices[0].message.content.strip()
            
            except Exception as e:
                error_type = type(e).__name__
                retries += 1
                
                # Check if error is retryable
                retryable_errors = [
                    'RateLimitError',
                    'APITimeoutError', 
                    'APIConnectionError',
                    'InternalServerError',
                    'Timeout'
                ]
                
                is_retryable = any(err in error_type for err in retryable_errors)
                
                if retries > max_retries or not is_retryable:
                    # Max retries reached or non-retryable error
                    print(f"Warning: LLM call failed: {e}")
                    self.retry_stats['failed_calls'] += 1
                    
                    # Use fallback
                    return self._fallback_response(scenario, facts, emotion)
                
                # Wait with exponential backoff
                print(f"   ⏳ LLM error ({error_type}), retrying in {backoff}s... (attempt {retries}/{max_retries})")
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff: 1s, 2s, 4s
                
                self.retry_stats['retries'] += 1
        
        # Should not reach here, but fallback just in case
        self.retry_stats['failed_calls'] += 1
        return self._fallback_response(scenario, facts, emotion)
    
    def _build_prompt(
        self,
        scenario: str,
        facts: Dict,
        constraints: List[str],
        emotion: str
    ) -> str:
        """Build user prompt"""
        
        prompt_parts = [f"Scenario: {scenario}"]
        
        # Add emotion context
        if emotion != "neutral":
            prompt_parts.append(f"Customer emotion: {emotion}")
        
        # Add facts
        if facts.get("order_data"):
            order = facts["order_data"]
            prompt_parts.append(f"Order: {order.get('order_id', 'N/A')} - Status: {order.get('status', 'unknown')}")
        
        if facts.get("knowledge_data"):
            knowledge = facts["knowledge_data"]
            if isinstance(knowledge, list) and knowledge:
                prompt_parts.append(f"Relevant info: {knowledge[0][:200]}")
        
        if facts.get("active_topic"):
            topic = facts["active_topic"]
            prompt_parts.append(f"Context: {topic.get('topic_type')} {topic.get('entity_id')}")
        
        if facts.get("escalation"):
            esc = facts["escalation"]
            prompt_parts.append(f"ESCALATION NEEDED: {esc.get('reason')}")
        
        if facts.get("empathy_needed"):
            prompt_parts.append("Show empathy before addressing issue")
        
        # Add constraints
        if constraints:
            prompt_parts.append(f"Constraints: {', '.join(constraints)}")
        
        return "\n".join(prompt_parts)
    
    def _build_system_prompt(
        self,
        brand_voice: Optional[Dict],
        constraints: List[str]
    ) -> str:
        """Build system prompt from brand voice"""
        
        base = "You are a helpful customer support agent."
        
        if brand_voice:
            tone = brand_voice.get('tone', 'professional')
            emoji = brand_voice.get('emoji_usage', 'moderate')
            
            base += f" Tone: {tone}."
            
            if emoji == 'frequent':
                base += " Use emojis frequently to be friendly."
            elif emoji == 'moderate':
                base += " Use emojis moderately."
            elif emoji == 'none':
                base += " Do not use emojis."
        
        if constraints:
            base += f" Constraints: {', '.join(constraints)}."
        
        return base
    
    def _fallback_response(
        self,
        scenario: str,
        facts: Dict,
        emotion: str
    ) -> str:
        """Generate fallback response when LLM fails"""
        
        # Check for escalation
        if facts.get('escalation'):
            return "I understand this is important. Let me connect you with our support team who can help you better."
        
        # Emotion-based fallbacks
        if emotion == "frustrated":
            return "I understand your concern and I'm here to help. Let me look into this for you right away."
        
        if emotion == "urgent":
            return "I understand this is urgent. Let me prioritize this and get you the information you need."
        
        # Scenario-based fallbacks
        if scenario == "order_status_query":
            return "I'm here to help with your order! Could you provide a bit more detail so I can assist you better?"
        
        if scenario == "policy_question":
            return "I want to give you accurate information about our policies. Let me connect you with our support team."
        
        # Generic fallback
        return "I'm here to help! Could you provide a bit more detail so I can assist you better?"
    
    def get_retry_stats(self) -> Dict:
        """Get retry statistics"""
        total = self.retry_stats['total_calls']
        success_rate = (self.retry_stats['successful_calls'] / total * 100) if total > 0 else 0
        
        return {
            **self.retry_stats,
            'success_rate': round(success_rate, 1)
        }
    
    def __repr__(self) -> str:
        stats = self.get_retry_stats()
        return f"LLMResponseComposer(model={self.model}, success_rate={stats['success_rate']}%)"
