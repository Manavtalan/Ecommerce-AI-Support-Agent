"""
Brand Voice Configuration
Loads and manages brand-specific voice settings
"""

from typing import Dict, List, Optional
from core.brands.registry import get_brand_registry


class BrandVoice:
    """Manages brand voice configuration and guidelines"""
    
    def __init__(self, brand_id: str):
        """
        Initialize brand voice
        
        Args:
            brand_id: Brand identifier
        """
        self.brand_id = brand_id
        
        # Load brand config
        registry = get_brand_registry()
        self.brand_config = registry.get_brand_by_id(brand_id)
        
        if not self.brand_config:
            raise ValueError(f"Brand {brand_id} not found")
        
        # Extract voice config
        self.voice_config = self.brand_config.get("voice", {})
    
    def get_tone(self) -> str:
        """
        Get brand tone
        
        Returns:
            Tone description (e.g., 'friendly_professional')
        """
        return self.voice_config.get("tone", "neutral")
    
    def get_formality(self) -> str:
        """
        Get formality level
        
        Returns:
            Formality level (e.g., 'casual', 'formal')
        """
        return self.voice_config.get("formality", "neutral")
    
    def get_emoji_usage(self) -> str:
        """
        Get emoji usage level
        
        Returns:
            Emoji usage (e.g., 'none', 'minimal', 'moderate', 'frequent')
        """
        return self.voice_config.get("emoji_usage", "none")
    
    def should_use_emojis(self) -> bool:
        """Check if brand uses emojis"""
        emoji_level = self.get_emoji_usage()
        return emoji_level not in ["none", ""]
    
    def get_emoji_preferences(self) -> Dict[str, str]:
        """
        Get brand's emoji preferences
        
        Returns:
            Dict of emoji types and their values
        """
        return self.voice_config.get("emoji_preferences", {})
    
    def get_signature_phrases(self) -> List[str]:
        """
        Get brand's signature phrases
        
        Returns:
            List of phrases the brand likes to use
        """
        return self.voice_config.get("signature_phrases", [])
    
    def get_forbidden_phrases(self) -> List[str]:
        """
        Get brand's forbidden phrases
        
        Returns:
            List of phrases to avoid
        """
        return self.voice_config.get("forbidden_phrases", [])
    
    def get_tone_description(self) -> str:
        """
        Get detailed tone description for system prompt
        
        Returns:
            Natural language description of tone
        """
        tone = self.get_tone()
        formality = self.get_formality()
        emoji = self.get_emoji_usage()
        
        # Build tone description
        descriptions = {
            "friendly_professional": "friendly yet professional, warm but maintaining expertise",
            "professional_technical": "professional and technical, precise and clear",
            "warm_health_focused": "warm and caring, with focus on health and wellness",
            "casual": "casual and conversational, like talking to a friend",
            "formal": "formal and professional, business-appropriate"
        }
        
        tone_desc = descriptions.get(tone, "helpful and clear")
        
        # Add formality
        if formality == "casual":
            tone_desc += ", using casual language"
        elif formality == "formal":
            tone_desc += ", maintaining formal communication"
        
        # Add emoji guidance
        if emoji == "none":
            tone_desc += ". Do not use emojis."
        elif emoji == "moderate":
            tone_desc += ". Use emojis moderately to add warmth."
        elif emoji == "frequent":
            tone_desc += ". Use emojis frequently to create a friendly atmosphere."
        
        return tone_desc
    
    def get_voice_guidelines(self) -> str:
        """
        Get complete voice guidelines for system prompt
        
        Returns:
            Formatted voice guidelines text
        """
        guidelines = []
        
        # Tone
        guidelines.append(f"TONE: {self.get_tone_description()}")
        
        # Signature phrases
        if self.get_signature_phrases():
            phrases = ", ".join(f'"{p}"' for p in self.get_signature_phrases()[:3])
            guidelines.append(f"USE PHRASES LIKE: {phrases}")
        
        # Forbidden phrases
        if self.get_forbidden_phrases():
            phrases = ", ".join(f'"{p}"' for p in self.get_forbidden_phrases()[:3])
            guidelines.append(f"AVOID PHRASES LIKE: {phrases}")
        
        # Emoji preferences
        if self.should_use_emojis():
            emoji_prefs = self.get_emoji_preferences()
            if emoji_prefs:
                examples = []
                for context, emoji in list(emoji_prefs.items())[:3]:
                    examples.append(f"{emoji} for {context}")
                guidelines.append(f"EMOJI EXAMPLES: {', '.join(examples)}")
        
        return "\n".join(guidelines)
    
    def __repr__(self) -> str:
        return f"BrandVoice(brand={self.brand_id}, tone={self.get_tone()})"


# Factory function
def load_brand_voice(brand_id: str) -> BrandVoice:
    """
    Load brand voice configuration
    
    Args:
        brand_id: Brand identifier
    
    Returns:
        BrandVoice instance
    """
    return BrandVoice(brand_id)
