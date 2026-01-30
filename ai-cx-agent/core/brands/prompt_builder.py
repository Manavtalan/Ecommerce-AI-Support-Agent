"""
System Prompt Builder
Generates brand-specific system prompts dynamically
"""

from typing import Dict, Optional
from core.brands.voice import BrandVoice
from core.brands.registry import get_brand_registry


class SystemPromptBuilder:
    """Builds brand-specific system prompts"""
    
    # Base system prompt (brand-agnostic)
    BASE_PROMPT = """You are a helpful AI customer support agent for {brand_name}.

Your primary goal is to help customers with their questions about orders, products, policies, and general inquiries. You have access to real-time order data, product information, and company policies.

CORE RESPONSIBILITIES:
- Answer customer questions accurately using available data
- Help track orders and resolve issues
- Explain policies clearly and helpfully
- Maintain the brand's voice and personality
- Escalate to human support when needed

IMPORTANT RULES:
- Always be honest - if you don't know something, say so
- Never make up order information or policies
- Use the tools available to fetch real data
- Respect customer privacy and data security
- Be patient with frustrated customers"""
    
    def __init__(self, brand_id: str):
        """
        Initialize prompt builder
        
        Args:
            brand_id: Brand identifier
        """
        self.brand_id = brand_id
        
        # Load brand config
        registry = get_brand_registry()
        self.brand_config = registry.get_brand_by_id(brand_id)
        
        if not self.brand_config:
            raise ValueError(f"Brand {brand_id} not found")
        
        # Load voice config
        self.voice = BrandVoice(brand_id)
    
    def build_system_prompt(self) -> str:
        """
        Build complete system prompt for brand
        
        Returns:
            Complete system prompt string
        """
        # Start with base
        prompt_parts = []
        
        # Add base prompt with brand name
        brand_name = self.brand_config.get("name", self.brand_id)
        base = self.BASE_PROMPT.format(brand_name=brand_name)
        prompt_parts.append(base)
        
        # Add voice guidelines
        voice_section = self._build_voice_section()
        prompt_parts.append(voice_section)
        
        # Add policy constraints
        policy_section = self._build_policy_section()
        prompt_parts.append(policy_section)
        
        # Add industry-specific context
        industry_section = self._build_industry_section()
        if industry_section:
            prompt_parts.append(industry_section)
        
        # Combine all parts
        return "\n\n".join(prompt_parts)
    
    def _build_voice_section(self) -> str:
        """Build voice and personality section"""
        brand_name = self.brand_config.get("name")
        
        section = f"""BRAND VOICE & PERSONALITY ({brand_name}):
{self.voice.get_voice_guidelines()}

COMMUNICATION STYLE:
{self.voice.get_tone_description()}"""
        
        return section
    
    def _build_policy_section(self) -> str:
        """Build policy constraints section"""
        policies = self.brand_config.get("policies", {})
        
        policy_lines = ["KEY POLICIES TO REMEMBER:"]
        
        # Return window
        if "return_window_days" in policies:
            policy_lines.append(f"- Return window: {policies['return_window_days']} days from delivery")
        
        # Free shipping
        if "free_shipping_threshold" in policies:
            policy_lines.append(f"- Free shipping on orders above ₹{policies['free_shipping_threshold']}")
        
        # COD
        if "cod_available" in policies:
            cod_status = "available" if policies["cod_available"] else "not available"
            policy_lines.append(f"- Cash on Delivery (COD): {cod_status}")
        
        # International shipping
        if "international_shipping" in policies:
            intl_status = "available" if policies["international_shipping"] else "India only"
            policy_lines.append(f"- International shipping: {intl_status}")
        
        return "\n".join(policy_lines)
    
    def _build_industry_section(self) -> Optional[str]:
        """Build industry-specific guidance"""
        industry = self.brand_config.get("industry", "")
        
        industry_guidance = {
            "fashion": """FASHION INDUSTRY CONTEXT:
- Emphasize style, fit, and quality
- Mention seasonal collections when relevant
- Be enthusiastic about fashion choices
- Address sizing concerns with care""",
            
            "technology": """TECHNOLOGY INDUSTRY CONTEXT:
- Be precise with technical specifications
- Provide clear troubleshooting steps
- Explain technical concepts clearly
- Emphasize product features and capabilities""",
            
            "food_health": """FOOD & HEALTH INDUSTRY CONTEXT:
- Emphasize freshness and quality
- Mention health benefits when relevant
- Be mindful of dietary preferences
- Show care for customer wellness"""
        }
        
        return industry_guidance.get(industry)
    
    def get_prompt_summary(self) -> Dict[str, str]:
        """Get summary of prompt components"""
        return {
            "brand": self.brand_config.get("name"),
            "tone": self.voice.get_tone(),
            "formality": self.voice.get_formality(),
            "emoji_usage": self.voice.get_emoji_usage(),
            "industry": self.brand_config.get("industry")
        }
    
    def __repr__(self) -> str:
        return f"SystemPromptBuilder(brand={self.brand_id})"


# Convenience function
def build_system_prompt(brand_id: str) -> str:
    """
    Build system prompt for brand
    
    Args:
        brand_id: Brand identifier
    
    Returns:
        Complete system prompt
    """
    builder = SystemPromptBuilder(brand_id)
    return builder.build_system_prompt()
