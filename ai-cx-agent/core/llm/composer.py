"""
LLM Response Composer
Handles structured response generation with scenario-based prompting
"""

import os
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMResponseComposer:
    """
    Composes natural, context-aware responses using LLM
    Prevents hallucinations by grounding responses in facts
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        # Initialize client here, not at module level
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self._client = OpenAI(api_key=api_key)
        return self._client
    
    def compose_response(
        self,
        scenario: str,
        facts: Dict,
        constraints: List[str] = None,
        emotion: str = "neutral",
        brand_voice: Optional[Dict] = None
    ) -> str:
        """
        Compose a response based on scenario and facts
        
        Args:
            scenario: Type of response needed (order_status, delay_explanation, etc.)
            facts: Verified facts to include (order details, tracking, etc.)
            constraints: What agent CANNOT do (cancel orders, process refunds, etc.)
            emotion: Detected customer emotion
            brand_voice: Brand voice guidelines (optional)
        
        Returns:
            Natural, empathetic response string
        """
        
        if constraints is None:
            constraints = []
        
        # Build system prompt
        system_prompt = self._build_system_prompt(brand_voice, constraints)
        
        # Build user prompt based on scenario
        user_prompt = self._build_scenario_prompt(scenario, facts, emotion)
        
        # Call LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Warning: LLM call failed: {e}")
            # Fallback response if LLM fails
            return self._fallback_response(scenario, facts, emotion)
    
    def _build_system_prompt(
        self,
        brand_voice: Optional[Dict],
        constraints: List[str]
    ) -> str:
        """Build system prompt with brand voice and constraints"""
        
        base_prompt = """You are a helpful customer support agent for an e-commerce brand.

Your communication style:
- Friendly and professional
- Empathetic and understanding
- Clear and concise
- Natural, not robotic

CRITICAL RULES:
- ONLY use information provided in the facts
- NEVER make up order numbers, dates, or tracking information
- If information is missing, acknowledge it
- Be honest about what you can and cannot do
"""
        
        # Add brand voice if provided
        if brand_voice:
            tone = brand_voice.get('tone', 'friendly_professional')
            formality = brand_voice.get('formality', 'casual')
            base_prompt += f"\n\nBrand Voice: {tone}, {formality} formality\n"
            
            if 'forbidden_phrases' in brand_voice:
                forbidden = ", ".join(brand_voice['forbidden_phrases'][:3])
                base_prompt += f"Never use phrases like: {forbidden}\n"
        
        # Add constraints
        if constraints:
            base_prompt += "\n\nYou CANNOT:\n"
            for constraint in constraints:
                base_prompt += f"- {constraint}\n"
        
        return base_prompt
    
    def _build_scenario_prompt(
        self,
        scenario: str,
        facts: Dict,
        emotion: str
    ) -> str:
        """Build scenario-specific prompt with facts"""
        
        # Emotion context
        emotion_context = ""
        if emotion == "frustrated":
            emotion_context = "The customer is frustrated. Show empathy FIRST, then provide solution."
        elif emotion == "confused":
            emotion_context = "The customer seems confused. Use simple, clear language."
        elif emotion == "urgent":
            emotion_context = "The customer needs urgent help. Be direct and action-oriented."
        
        # Scenario templates
        scenarios = {
            "order_status_simple": f"""
{emotion_context}

Customer asked about their order status.

FACTS:
{self._format_facts(facts)}

Provide the order status in a natural, friendly way. Include tracking information if available.
""",
            
            "delay_explanation": f"""
{emotion_context}

Customer's order is delayed and they're asking about it.

FACTS:
{self._format_facts(facts)}

Explain the delay with empathy, provide revised ETA, and reassure the customer.
""",
            
            "frustrated_customer": f"""
The customer is FRUSTRATED or ANGRY.

FACTS:
{self._format_facts(facts)}

Respond with:
1. EMPATHY first (acknowledge their frustration)
2. EXPLANATION (what happened)
3. SOLUTION (what you're doing about it)
4. REASSURANCE

Be warm and understanding. This is critical for customer satisfaction.
""",
            
            "policy_question": f"""
{emotion_context}

Customer asked about a policy.

POLICY INFORMATION:
{self._format_facts(facts)}

Explain the policy in simple, customer-friendly terms. Be helpful.
""",
            
            "general_query": f"""
{emotion_context}

Customer asked a question.

AVAILABLE INFORMATION:
{self._format_facts(facts)}

Provide a helpful, natural response. If you don't have enough information, ask for clarification.
"""
        }
        
        return scenarios.get(scenario, scenarios["general_query"])
    
    def _format_facts(self, facts: Dict) -> str:
        """Format facts dictionary into readable text"""
        formatted = []
        for key, value in facts.items():
            formatted.append(f"- {key}: {value}")
        return "\n".join(formatted) if formatted else "No specific facts provided"
    
    def _fallback_response(
        self,
        scenario: str,
        facts: Dict,
        emotion: str
    ) -> str:
        """Fallback response if LLM fails"""
        
        if emotion == "frustrated":
            return "I understand your concern and I'm here to help. Let me look into this for you right away."
        
        if scenario == "order_status_simple" and "order_id" in facts:
            return f"Let me check on order {facts['order_id']} for you."
        
        return "I'm here to help! Could you provide a bit more detail so I can assist you better?"


# Singleton instance
_composer_instance = None

def get_composer() -> LLMResponseComposer:
    """Get singleton composer instance"""
    global _composer_instance
    if _composer_instance is None:
        _composer_instance = LLMResponseComposer()
    return _composer_instance
