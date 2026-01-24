# emotion_detector.py
"""
Detects customer emotions from their messages.
Simple keyword-based detection (no AI needed).
"""

from typing import Tuple
import re


class EmotionDetector:
    """Detects customer emotional state for tone adjustment"""
    
    # Keywords that indicate frustration
    FRUSTRATION_KEYWORDS = [
        "frustrated", "frustrating", "annoyed", "angry",
        "ridiculous", "terrible", "awful", "worst",
        "disappointed", "upset", "mad", 
        "late", "delayed", "slow", "long", "why"  # Delay-related
    ]
    
    # Keywords that indicate urgency
    URGENCY_KEYWORDS = [
        "urgent", "asap", "immediately", "now", "today",
        "emergency", "critical", "right away"
    ]
    
    # Keywords that indicate confusion
    CONFUSION_KEYWORDS = [
        "confused", "confusing", "don't understand", 
        "unclear", "explain", "not sure"
    ]
    
    # Keywords that indicate positive sentiment
    POSITIVE_KEYWORDS = [
        "thanks", "thank you", "appreciate", "great",
        "perfect", "excellent", "helpful", "good"
    ]
    
    @staticmethod
    def detect_emotion(message: str, conversation_history=None) -> Tuple[str, int, dict]:
        """
        Detect emotion from customer message.
        
        Args:
            message: The customer's message
            conversation_history: Not used yet (for future)
            
        Returns:
            (emotion, intensity, indicators)
            - emotion: "neutral", "frustrated", "angry", "urgent", "confused", "positive"
            - intensity: 0-10 (how strong the emotion is)
            - indicators: Dict with detected keywords
        """
        msg_lower = message.lower().strip()
        
        # Track what we found
        indicators = {
            "frustration_words": [],
            "urgency_words": [],
            "confusion_words": [],
            "positive_words": [],
            "caps_usage": 0,
            "repeated_punctuation": False
        }
        
        # Check for frustration keywords
        for word in EmotionDetector.FRUSTRATION_KEYWORDS:
            if word in msg_lower:
                indicators["frustration_words"].append(word)
        
        # Check for urgency keywords
        for word in EmotionDetector.URGENCY_KEYWORDS:
            if word in msg_lower:
                indicators["urgency_words"].append(word)
        
        # Check for confusion keywords
        for word in EmotionDetector.CONFUSION_KEYWORDS:
            if word in msg_lower:
                indicators["confusion_words"].append(word)
        
        # Check for positive keywords
        for word in EmotionDetector.POSITIVE_KEYWORDS:
            if word in msg_lower:
                indicators["positive_words"].append(word)
        
        # Check caps lock (SHOUTING)
        if len(message) > 5:
            caps_count = sum(1 for c in message if c.isupper())
            total_letters = sum(1 for c in message if c.isalpha())
            if total_letters > 0:
                indicators["caps_usage"] = caps_count / total_letters
        
        # Check repeated punctuation (!!!, ???)
        if re.search(r'[!?]{2,}', message):
            indicators["repeated_punctuation"] = True
        
        # Calculate emotion and intensity
        emotion, intensity = EmotionDetector._calculate_emotion_score(indicators)
        
        return emotion, intensity, indicators
    
    @staticmethod
    def _calculate_emotion_score(indicators: dict) -> Tuple[str, int]:
        """Calculate the primary emotion and its intensity"""
        
        emotion = "neutral"
        intensity = 0
        
        # Count frustration words
        frustration_count = len(indicators["frustration_words"])
        
        if frustration_count >= 2:
            # Multiple frustration words = definitely frustrated
            emotion = "frustrated"
            intensity = min(frustration_count * 2 + 5, 10)
            
            # If also SHOUTING, upgrade to angry
            if indicators["caps_usage"] > 0.5:
                emotion = "angry"
                intensity = 9
                
        elif frustration_count == 1:
            # One frustration word = mildly frustrated
            emotion = "frustrated"
            intensity = 4
        
        # Check urgency
        urgency_count = len(indicators["urgency_words"])
        if urgency_count > 0 and emotion == "neutral":
            emotion = "urgent"
            intensity = min(urgency_count * 2 + 4, 10)
        
        # Check confusion
        confusion_count = len(indicators["confusion_words"])
        if confusion_count > 0 and emotion == "neutral":
            emotion = "confused"
            intensity = 3
        
        # Check positive
        positive_count = len(indicators["positive_words"])
        if positive_count > 0 and emotion == "neutral":
            emotion = "positive"
            intensity = 2
        
        return emotion, intensity