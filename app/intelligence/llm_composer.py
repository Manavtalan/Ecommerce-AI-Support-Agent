# llm_composer.py
"""
LLM Response Composer - The AI Communication Layer
This is the ONLY place where AI generates customer-facing responses.

ARCHITECTURE:
- Facts come from code (deterministic)
- Words come from AI (this module)
- Business logic NEVER lives in prompts
"""

from openai import OpenAI
from config import OPENAI_API_KEY
from typing import Dict, List, Optional
import json

client = OpenAI(api_key=OPENAI_API_KEY)


# ============================================================================
# SYSTEM PROMPTS - The AI's Communication Instructions
# ============================================================================

BASE_COMMUNICATION_PROMPT = """
You are a highly skilled customer support agent communication layer.

YOUR ROLE:
- Transform facts into natural, empathetic responses
- Explain policies clearly and warmly
- Reassure customers while staying truthful
- Adapt tone based on customer emotion

YOUR CONSTRAINTS:
- Use ONLY the facts provided to you
- NEVER invent order details, dates, or tracking info
- NEVER promise actions outside your allowed scope
- NEVER override business policies

YOUR STYLE:
- Sound like a real human, not a chatbot
- Be warm but professional
- Acknowledge emotions before facts
- Offer help, not excuses
- Keep responses conversational (2-4 paragraphs)

FORBIDDEN PHRASES:
- "I apologize for the inconvenience" (overused)
- "Please be patient" (condescending)
- "Unfortunately..." without offering alternatives
- Any invented facts or promises
"""


SCENARIO_PROMPTS = {
    "delay_explanation": """
SCENARIO: Customer asking why their order is delayed/taking long

YOUR TASK:
1. Acknowledge their concern about the wait
2. Explain the situation using ONLY provided facts
3. Provide context (seasonality, courier networks, etc.) IF delay is normal
4. Reassure with concrete next steps
5. Offer tracking or other helpful options

TONE: Empathetic, transparent, action-oriented
""",
    
    "cancellation_request": """
SCENARIO: Customer wants to cancel their order

YOUR TASK:
1. Acknowledge their request warmly
2. Explain current order status clearly
3. If cancellation is NOT possible, explain WHY (based on facts)
4. Offer alternatives (return process, etc.)
5. Give customer control over next steps

TONE: Understanding, honest, solution-focused
DO NOT: Immediately escalate without explaining options
""",
    
    "frustration_response": """
SCENARIO: Customer is frustrated or upset

YOUR TASK:
1. Acknowledge the emotion directly and sincerely
2. Take responsibility for the experience
3. Provide clarity on what happened
4. Offer immediate next steps
5. Show you're personally invested in helping

TONE: Calm, apologetic, empowering
PRIORITY: De-escalate emotion before solving problem
""",
    
    "order_status_simple": """
SCENARIO: Straightforward order status query

YOUR TASK:
1. Provide status clearly and positively
2. Include key details (courier, ETA, tracking)
3. Proactively offer related help
4. Keep it brief but warm

TONE: Helpful, efficient, friendly
""",
    
    "order_not_found": """
SCENARIO: Order number not found in system

YOUR TASK:
1. Acknowledge the issue without blame
2. Offer possible explanations
3. Suggest concrete next steps
4. Offer to help investigate

TONE: Helpful, not accusatory, solution-focused
""",
    
    "policy_explanation": """
SCENARIO: Explaining a policy (returns, refunds, etc.)

YOUR TASK:
1. Explain the policy clearly and simply
2. Provide the reasoning behind it
3. Highlight what IS possible within policy
4. Offer to answer specific questions

TONE: Transparent, fair, helpful
""",
    
    "proactive_followup": """
SCENARIO: Offering additional help after answering main query

YOUR TASK:
1. Briefly suggest related helpful actions
2. Don't be pushy or sales-y
3. Give customer easy next steps
4. Show you're thinking ahead for them

TONE: Thoughtful, optional, genuinely helpful
"""
}


# ============================================================================
# LLM Response Composer - Single Entry Point for All AI Communication
# ============================================================================

class LLMResponseComposer:
    """
    The single source of AI-generated customer communication.
    
    NEVER call OpenAI directly from other modules.
    ALL customer-facing AI text goes through this class.
    """
    
    def __init__(self, brand_config: Optional[Dict] = None):
        """
        Initialize composer with optional brand customization.
        
        Args:
            brand_config: Brand voice settings (tone, personality, etc.)
        """
        self.brand_config = brand_config or {}
        self.default_tone = self.brand_config.get("tone", "friendly_professional")
    
    def compose_response(
        self,
        scenario: str,
        facts: Dict,
        constraints: List[str],
        emotion: str = "neutral",
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Compose a natural language response using AI.
        
        This is the ONLY method that should be called from outside this module.
        
        Args:
            scenario: Type of response needed (e.g., "delay_explanation")
            facts: Dictionary of verified facts to use in response
            constraints: List of what AI cannot do/promise
            emotion: Detected customer emotion ("neutral", "frustrated", "confused")
            custom_instructions: Optional additional guidance for this specific case
            
        Returns:
            Natural language response as string
            
        Example:
            response = composer.compose_response(
                scenario="delay_explanation",
                facts={
                    "order_id": "12345",
                    "status": "shipped",
                    "eta": "2026-01-25",
                    "days_since_order": 10
                },
                constraints=["cannot_cancel", "cannot_change_delivery_date"],
                emotion="frustrated"
            )
        """
        
        # Build the complete prompt
        system_prompt = self._build_system_prompt(scenario, emotion)
        user_prompt = self._build_user_prompt(facts, constraints, custom_instructions)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Higher for natural variation
                max_tokens=400,
                presence_penalty=0.3,  # Reduce repetitive phrasing
                frequency_penalty=0.3
            )
            
            generated_response = response.choices[0].message.content
            
            # Validate response (check for hallucinations)
            if self._contains_hallucination(generated_response, facts):
                # Fallback to safe response
                return self._safe_fallback_response(scenario, facts)
            
            return generated_response
            
        except Exception as e:
            # If AI fails, return safe fallback
            print(f"[LLM COMPOSER ERROR] {e}")
            return self._safe_fallback_response(scenario, facts)
    
    def _build_system_prompt(self, scenario: str, emotion: str) -> str:
        """Build the system prompt based on scenario and emotion."""
        
        # Start with base communication rules
        prompt = BASE_COMMUNICATION_PROMPT
        
        # Add scenario-specific instructions
        if scenario in SCENARIO_PROMPTS:
            prompt += "\n\n" + SCENARIO_PROMPTS[scenario]
        
        # Adjust for customer emotion
        if emotion == "frustrated":
            prompt += "\n\nCUSTOMER EMOTION: FRUSTRATED - Prioritize empathy and de-escalation"
        elif emotion == "confused":
            prompt += "\n\nCUSTOMER EMOTION: CONFUSED - Prioritize clarity and simple language"
        elif emotion == "urgent":
            prompt += "\n\nCUSTOMER EMOTION: URGENT - Acknowledge urgency, provide immediate next steps"
        
        # Add brand voice if configured
        if self.brand_config:
            prompt += self._inject_brand_voice()
        
        return prompt
    
    def _build_user_prompt(
        self,
        facts: Dict,
        constraints: List[str],
        custom_instructions: Optional[str]
    ) -> str:
        """Build the user prompt with facts and constraints."""
        
        prompt = "Generate a customer support response using these details:\n\n"
        
        # Add facts
        prompt += "FACTS (use ONLY these, never invent):\n"
        for key, value in facts.items():
            prompt += f"- {key}: {value}\n"
        
        # Add constraints
        if constraints:
            prompt += "\nCONSTRAINTS (what you CANNOT do/promise):\n"
            for constraint in constraints:
                prompt += f"- {constraint}\n"
        
        # Add custom instructions if provided
        if custom_instructions:
            prompt += f"\nADDITIONAL GUIDANCE:\n{custom_instructions}\n"
        
        prompt += "\nGenerate the response now:"
        
        return prompt
    
    def _inject_brand_voice(self) -> str:
        """Inject brand-specific voice instructions."""
        
        voice_prompt = "\n\nBRAND VOICE:"
        
        if "personality" in self.brand_config:
            traits = ", ".join(self.brand_config["personality"])
            voice_prompt += f"\n- Personality: {traits}"
        
        if "signature_phrases" in self.brand_config:
            phrases = ", ".join(self.brand_config["signature_phrases"])
            voice_prompt += f"\n- Encouraged phrases: {phrases}"
        
        if "avoid_phrases" in self.brand_config:
            avoid = ", ".join(self.brand_config["avoid_phrases"])
            voice_prompt += f"\n- Avoid: {avoid}"
        
        return voice_prompt
    
    def _contains_hallucination(self, response: str, facts: Dict) -> bool:
        """
        Check if AI response contains hallucinated information.
        
        Returns True if hallucination detected, False if safe.
        """
        
        # Common hallucination indicators
        hallucination_phrases = [
            "I'll cancel that for you",
            "I've processed the refund",
            "I'll upgrade your shipping",
            "tracking number is",
            "order number is"
        ]
        
        response_lower = response.lower()
        
        # Check for forbidden promises
        for phrase in hallucination_phrases:
            if phrase in response_lower:
                print(f"[HALLUCINATION DETECTED] Phrase: {phrase}")
                return True
        
        # Check if response invents facts not in provided facts
        # (This is a simple heuristic - can be enhanced)
        
        return False
    
    def _safe_fallback_response(self, scenario: str, facts: Dict) -> str:
        """
        Generate a safe, deterministic response when AI fails or hallucinates.
        """
        
        order_id = facts.get("order_id", "your order")
        
        fallback_responses = {
            "delay_explanation": f"I understand you're asking about the delivery timeline for {order_id}. Let me connect you with our support team who can provide detailed information and help resolve any concerns.",
            
            "cancellation_request": f"I'd like to help with your cancellation request for {order_id}. Let me connect you with our team who can review the order status and discuss your options.",
            
            "order_status_simple": f"I have information about {order_id}. Let me get you to someone who can share the full details.",
            
            "default": "I want to make sure I give you accurate information. Let me connect you with our support team who can help you right away."
        }
        
        return fallback_responses.get(scenario, fallback_responses["default"])


# ============================================================================
# Helper Functions
# ============================================================================

def quick_compose(scenario: str, facts: Dict, constraints: List[str] = None) -> str:
    """
    Quick wrapper for simple one-off compositions.
    
    For most use cases, instantiate LLMResponseComposer and reuse it.
    """
    composer = LLMResponseComposer()
    return composer.compose_response(
        scenario=scenario,
        facts=facts,
        constraints=constraints or []
    )


