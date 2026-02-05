"""
LLM Response Composer - INTELLIGENT VERSION
Generates contextual responses with ACTUAL DATA USAGE
"""

from typing import Dict, List, Optional
from openai import OpenAI
import os
import time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class LLMResponseComposer:
    """Composes intelligent LLM responses that actually use tool data"""
    
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
        Compose intelligent response using tool data
        
        Args:
            scenario: Type of scenario
            facts: Context and facts (includes tool results)
            constraints: Response constraints
            emotion: Detected emotion
            brand_voice: Brand voice configuration
            system_prompt: Custom system prompt
            max_retries: Maximum retry attempts
        
        Returns:
            Generated response string
        """
        self.retry_stats['total_calls'] += 1
        
        retries = 0
        backoff = 1.0
        
        while retries <= max_retries:
            try:
                # Build INTELLIGENT prompt with data analysis
                user_prompt = self._build_intelligent_prompt(scenario, facts, constraints, emotion)
                
                # Use custom system prompt or build intelligent default
                if system_prompt:
                    sys_prompt = system_prompt
                else:
                    sys_prompt = self._build_intelligent_system_prompt(brand_voice)
                
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
                    print(f"Warning: LLM call failed: {e}")
                    self.retry_stats['failed_calls'] += 1
                    return self._intelligent_fallback(scenario, facts, emotion)
                
                print(f"   ⏳ LLM error ({error_type}), retrying in {backoff}s... (attempt {retries}/{max_retries})")
                time.sleep(backoff)
                backoff *= 2
                
                self.retry_stats['retries'] += 1
        
        self.retry_stats['failed_calls'] += 1
        return self._intelligent_fallback(scenario, facts, emotion)
    
    def _build_intelligent_prompt(
        self,
        scenario: str,
        facts: Dict,
        constraints: List[str],
        emotion: str
    ) -> str:
        """Build INTELLIGENT prompt that tells LLM to USE THE DATA"""
        
        prompt_parts = []
        
        # Add emotion context with empathy instruction
        if emotion == "frustrated":
            prompt_parts.append("⚠️ CUSTOMER IS FRUSTRATED - Show empathy first, then provide solution")
        elif emotion == "urgent":
            prompt_parts.append("⚠️ URGENT REQUEST - Acknowledge urgency and provide immediate help")
        
        # Add escalation if needed
        if facts.get("escalation"):
            esc = facts["escalation"]
            return f"ESCALATION REQUIRED: {esc.get('suggested_message', 'Let me connect you with our support team.')}"
        
        # === ORDER DATA - BE SPECIFIC ===
        if facts.get("order_data"):
            order = facts["order_data"]
            
            prompt_parts.append("📦 ORDER INFORMATION (USE THIS DATA IN YOUR RESPONSE):")
            prompt_parts.append(f"  Order ID: #{order.get('order_id')}")
            prompt_parts.append(f"  Customer: {order.get('customer_name')}")
            prompt_parts.append(f"  Status: {order.get('status', 'unknown').upper()}")
            
            # Items
            items = order.get('items', [])
            if items:
                prompt_parts.append(f"  Items ordered:")
                for item in items:
                    prompt_parts.append(f"    • {item.get('name')} ({item.get('color')}, Size {item.get('size')}) - Qty: {item.get('quantity')}")
            
            # Shipping details
            shipping = order.get('shipping', {})
            if shipping:
                prompt_parts.append(f"  Shipping Status:")
                prompt_parts.append(f"    • Courier: {shipping.get('courier')}")
                prompt_parts.append(f"    • Tracking: {shipping.get('tracking_number')}")
                prompt_parts.append(f"    • Shipped Date: {shipping.get('shipped_date')}")
                prompt_parts.append(f"    • Estimated Delivery: {shipping.get('estimated_delivery')}")
                prompt_parts.append(f"    • Last Update: {shipping.get('last_update')}")
                prompt_parts.append(f"    • Current Location: {shipping.get('current_location')}")
            
            prompt_parts.append("")
            prompt_parts.append("🎯 YOUR TASK: Tell the customer about their SPECIFIC order using the details above.")
            prompt_parts.append("   - Mention the item name, color, and size")
            prompt_parts.append("   - Give them the tracking number")
            prompt_parts.append("   - Tell them the estimated delivery date")
            prompt_parts.append("   - Use the 'Last Update' to tell them where it is now")
        
        # === KNOWLEDGE DATA ===
        if facts.get("knowledge_data"):
            knowledge = facts["knowledge_data"]
            prompt_parts.append("")
            prompt_parts.append("📚 RELEVANT POLICY INFORMATION:")
            
            if isinstance(knowledge, list):
                for i, chunk in enumerate(knowledge[:3], 1):  # Top 3 chunks
                    prompt_parts.append(f"  [{i}] {chunk[:300]}")
            elif isinstance(knowledge, str):
                prompt_parts.append(f"  {knowledge[:500]}")
            
            prompt_parts.append("")
            prompt_parts.append("🎯 YOUR TASK: Answer the policy question using the information above.")
            prompt_parts.append("   - Be specific about policies")
            prompt_parts.append("   - Quote relevant parts if helpful")
        
        # === PRODUCT DATA ===
        if facts.get("product_data"):
            product = facts["product_data"]
            prompt_parts.append("")
            prompt_parts.append("👕 PRODUCT INFORMATION:")
            prompt_parts.append(f"  Product: {product.get('name')}")
            prompt_parts.append(f"  Price: ₹{product.get('price')}")
            prompt_parts.append(f"  Available Sizes: {', '.join(product.get('sizes', []))}")
            prompt_parts.append(f"  Available Colors: {', '.join(product.get('colors', []))}")
            prompt_parts.append(f"  In Stock: {'Yes' if product.get('in_stock') else 'No'}")
        
        # === SHIPPING DATA ===
        if facts.get("shipping_data"):
            shipping = facts["shipping_data"]
            prompt_parts.append("")
            prompt_parts.append("🚚 SHIPPING INFORMATION:")
            prompt_parts.append(f"  Location: {shipping.get('location')}")
            prompt_parts.append(f"  Available: {'Yes' if shipping.get('available') else 'No'}")
            prompt_parts.append(f"  Estimated Days: {shipping.get('estimated_days')}")
            prompt_parts.append(f"  Cost: ₹{shipping.get('cost')}")
        
        # === CONTEXT ===
        if facts.get("active_topic"):
            topic = facts["active_topic"]
            prompt_parts.append("")
            prompt_parts.append(f"💭 CONVERSATION CONTEXT: Customer is discussing {topic.get('topic_type')} {topic.get('entity_id')}")
        
        # === EMPATHY INSTRUCTION ===
        if facts.get("empathy_needed"):
            prompt_parts.append("")
            prompt_parts.append("💚 IMPORTANT: Show empathy and understanding BEFORE providing information")
        
        # === INTELLIGENCE ANALYSIS ===
        if facts.get("intelligence_analysis"):
            intel = facts["intelligence_analysis"]
            prompt_parts.append("")
            prompt_parts.append("="*70)
            prompt_parts.append("🧠 INTELLIGENT ANALYSIS OF USER QUESTION:")
            prompt_parts.append("="*70)
            
            if intel.get('special_instructions'):
                prompt_parts.append(intel['special_instructions'])
            
            if intel.get('delay_analysis'):
                delay = intel['delay_analysis']
                prompt_parts.append("")
                prompt_parts.append("📊 DELAY ANALYSIS:")
                prompt_parts.append(f"  Is Late: {delay['is_late']}")
                prompt_parts.append(f"  Explanation: {delay['explanation']}")
            
            prompt_parts.append("="*70)
            prompt_parts.append("")
        
        # === TOOL ERROR HANDLING ===
        if facts.get("tool_error"):
            prompt_parts.append("")
            prompt_parts.append(f"⚠️ TOOL ERROR: {facts['tool_error']}")
            prompt_parts.append("🎯 YOUR TASK: Apologize politely and ask for more information or offer alternative help")
        
        # Add scenario
        prompt_parts.insert(0, f"SCENARIO: {scenario}")
        prompt_parts.insert(1, "")
        
        return "\n".join(prompt_parts)
    
    def _build_intelligent_system_prompt(
        self,
        brand_voice: Optional[Dict]
    ) -> str:
        """Build intelligent system prompt"""
        
        prompt = """You are an intelligent customer support agent.

🎯 YOUR PRIMARY GOAL: Be HELPFUL and SPECIFIC using the data provided.

CRITICAL RULES:
1. ALWAYS use specific details from the data (order items, tracking numbers, dates, etc.)
2. NEVER give generic responses like "Your order has been shipped!" - be specific!
3. If customer asks "what's in my order?" - LIST THE ITEMS with colors and sizes
4. If customer asks "why is it late?" - COMPARE dates and give real analysis
5. If customer asks "where is it?" - Give the CURRENT LOCATION from shipping data
6. Use natural, conversational language - don't sound robotic
7. Don't repeat yourself - each response should add new information

EXAMPLES OF GOOD vs BAD:

❌ BAD: "Your order has been shipped! 🎉"
✅ GOOD: "Your order #12345 (Summer Floral Dress in Blue, Size M) shipped on Jan 25th via Delhivery. It's currently at Bangalore Local Office and should arrive tomorrow (Jan 29th). Tracking: DEL123456789"

❌ BAD: "Let me help you with that!"
✅ GOOD: "Looking at your order, you have a Summer Floral Dress that should arrive by Jan 29th."

❌ BAD: "Your order is on the way!"
✅ GOOD: "Your dress is currently out for delivery in Bangalore and will reach you by tomorrow."
"""
        
        if brand_voice:
            tone = brand_voice.get('tone', 'professional')
            emoji = brand_voice.get('emoji_usage', 'moderate')
            formality = brand_voice.get('formality', 'casual')
            
            prompt += f"\n\nBRAND VOICE:"
            prompt += f"\n- Tone: {tone}"
            prompt += f"\n- Formality: {formality}"
            
            if emoji == 'frequent':
                prompt += "\n- Emojis: Use frequently (2-3 per response)"
            elif emoji == 'moderate':
                prompt += "\n- Emojis: Use moderately (1-2 per response)"
            elif emoji == 'minimal':
                prompt += "\n- Emojis: Use sparingly (0-1 per response)"
            else:
                prompt += "\n- Emojis: Don't use"
            
            if brand_voice.get('personality'):
                prompt += f"\n- Personality: {brand_voice['personality']}"
        
        return prompt
    
    def _intelligent_fallback(
        self,
        scenario: str,
        facts: Dict,
        emotion: str
    ) -> str:
        """Generate intelligent fallback when LLM fails"""
        
        # Escalation
        if facts.get('escalation'):
            return "I understand this is important. Let me connect you with our support team who can help you right away."
        
        # Order with data
        if facts.get("order_data"):
            order = facts["order_data"]
            items = order.get('items', [])
            shipping = order.get('shipping', {})
            
            response = f"Your order #{order.get('order_id')} "
            
            if items:
                item_names = ", ".join([item.get('name', 'item') for item in items])
                response += f"({item_names}) "
            
            response += f"is {order.get('status', 'being processed')}."
            
            if shipping.get('estimated_delivery'):
                response += f" Expected delivery: {shipping.get('estimated_delivery')}."
            
            if shipping.get('tracking_number'):
                response += f" Tracking: {shipping.get('tracking_number')}"
            
            return response
        
        # Emotion-based fallbacks
        if emotion == "frustrated":
            return "I understand your frustration. Let me help you resolve this right away. Could you provide more details?"
        
        if emotion == "urgent":
            return "I understand this is urgent. Let me prioritize this for you. What specific information do you need?"
        
        # Generic but helpful
        return "I'm here to help! Could you tell me more about what you need assistance with?"
    
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
