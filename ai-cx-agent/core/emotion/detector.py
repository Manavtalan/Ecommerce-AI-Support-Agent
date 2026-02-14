"""
Emotion Detector
Detects customer emotions from messages.
Handles keywords, emojis, caps, sarcasm, and punctuation patterns.
"""

from typing import Tuple
import re


class EmotionDetector:
    """Detects customer emotional state for tone adjustment"""

    # ── Emoji maps ──────────────────────────────────────────────────────────
    SAD_EMOJIS = {'😢', '😭', '😔', '😞', '😟', '🥺', '💔', '😿'}
    ANGRY_EMOJIS = {'😡', '🤬', '😤', '👿', '💢', '🖕'}
    HAPPY_EMOJIS = {'😊', '😄', '😁', '🙂', '😀', '🎉', '👍', '❤️', '😍'}
    SARCASM_EMOJIS = {'🙄', '😒', '😑', '🤦', '🤦‍♂️', '🤦‍♀️', '🙃'}

    # ── Keyword lists ────────────────────────────────────────────────────────
    SEVERE_FRUSTRATION_KEYWORDS = [
        'ridiculous', 'unacceptable', 'terrible', 'worst', 'awful',
        'disgusting', 'pathetic', 'outrageous', 'useless', 'incompetent',
        'lawsuit', 'complaint', 'scam', 'fraud', 'refund now', 'demand'
    ]

    FRUSTRATION_KEYWORDS = [
        'frustrated', 'frustrating', 'annoyed', 'angry', 'mad',
        'disappointed', 'upset', 'horrible', 'ruined', 'broken promise',
        'never again', 'wasted', 'ripped off'
    ]

    URGENCY_KEYWORDS = [
        'urgent', 'asap', 'immediately', 'right now', 'right away',
        'today', 'emergency', 'critical', 'can\'t wait', 'need it now'
    ]

    CONFUSION_KEYWORDS = [
        'confused', 'confusing', 'don\'t understand', 'dont understand',
        'unclear', 'not sure', 'what does', 'what do you mean', 'explain'
    ]

    POSITIVE_KEYWORDS = [
        'perfect', 'excellent', 'awesome', 'amazing', 'love it',
        'great service', 'very helpful', 'really happy', 'so happy'
    ]

    # Sarcasm patterns — positive words following a complaint context
    SARCASM_PHRASES = [
        'oh great', 'oh fantastic', 'oh wonderful', 'oh perfect',
        'thanks a lot', 'thanks so much', 'great job', 'well done',
        'oh sure', 'yeah right', 'of course it did', 'as expected',
        'what a surprise', 'shocking', 'love how', 'love that'
    ]

    # Words that indicate sarcasm when combined with complaint context
    COMPLAINT_CONTEXT_WORDS = [
        'again', 'still', 'another', 'yet again', 'always', 'never',
        'delay', 'wrong', 'broken', 'missing', 'lost', 'failed'
    ]

    @staticmethod
    def detect_emotion(message: str, conversation_history=None) -> Tuple[str, int, dict]:
        """
        Detect emotion from customer message.

        Returns:
            (emotion, intensity, indicators)
            - emotion: "neutral", "frustrated", "angry", "urgent",
                       "confused", "positive", "sad", "sarcastic"
            - intensity: 0-10
            - indicators: dict of what was detected
        """
        msg_lower = message.lower().strip()

        indicators = {
            "frustration_words": [],
            "severe_frustration_words": [],
            "urgency_words": [],
            "confusion_words": [],
            "positive_words": [],
            "sarcasm_phrases": [],
            "sad_emojis": [],
            "angry_emojis": [],
            "happy_emojis": [],
            "sarcasm_emojis": [],
            "caps_ratio": 0.0,
            "repeated_punctuation": False,
            "has_complaint_context": False
        }

        # ── Emoji detection ──────────────────────────────────────────────────
        for char in message:
            if char in EmotionDetector.ANGRY_EMOJIS:
                indicators["angry_emojis"].append(char)
            elif char in EmotionDetector.SAD_EMOJIS:
                indicators["sad_emojis"].append(char)
            elif char in EmotionDetector.SARCASM_EMOJIS:
                indicators["sarcasm_emojis"].append(char)
            elif char in EmotionDetector.HAPPY_EMOJIS:
                indicators["happy_emojis"].append(char)

        # ── Keyword detection ─────────────────────────────────────────────────
        for word in EmotionDetector.SEVERE_FRUSTRATION_KEYWORDS:
            if word in msg_lower:
                indicators["severe_frustration_words"].append(word)

        for word in EmotionDetector.FRUSTRATION_KEYWORDS:
            if word in msg_lower:
                indicators["frustration_words"].append(word)

        for word in EmotionDetector.URGENCY_KEYWORDS:
            if word in msg_lower:
                indicators["urgency_words"].append(word)

        for word in EmotionDetector.CONFUSION_KEYWORDS:
            if word in msg_lower:
                indicators["confusion_words"].append(word)

        for word in EmotionDetector.POSITIVE_KEYWORDS:
            if word in msg_lower:
                indicators["positive_words"].append(word)

        # ── Sarcasm phrase detection ─────────────────────────────────────────
        for phrase in EmotionDetector.SARCASM_PHRASES:
            if phrase in msg_lower:
                indicators["sarcasm_phrases"].append(phrase)

        # Check if message has complaint context words (strengthens sarcasm signal)
        for word in EmotionDetector.COMPLAINT_CONTEXT_WORDS:
            if word in msg_lower:
                indicators["has_complaint_context"] = True
                break

        # ── Caps ratio ───────────────────────────────────────────────────────
        if len(message) > 5:
            total_letters = sum(1 for c in message if c.isalpha())
            if total_letters > 0:
                caps_count = sum(1 for c in message if c.isupper())
                indicators["caps_ratio"] = caps_count / total_letters

        # ── Repeated punctuation ─────────────────────────────────────────────
        if re.search(r'[!?]{2,}', message):
            indicators["repeated_punctuation"] = True

        # ── Score ────────────────────────────────────────────────────────────
        emotion, intensity = EmotionDetector._calculate_emotion_score(indicators)

        return emotion, intensity, indicators

    @staticmethod
    def _calculate_emotion_score(indicators: dict) -> Tuple[str, int]:
        """
        Priority order:
        angry > sarcastic > frustrated > sad > urgent > confused > positive > neutral
        """

        # ── ANGRY ────────────────────────────────────────────────────────────
        # Severe words OR angry emojis OR SHOUTING + frustration
        severe_count = len(indicators["severe_frustration_words"])
        angry_emoji_count = len(indicators["angry_emojis"])
        is_shouting = indicators["caps_ratio"] > 0.5 and len(indicators["frustration_words"]) > 0

        if severe_count >= 1 or angry_emoji_count >= 1 or is_shouting:
            intensity = min(7 + severe_count + angry_emoji_count, 10)
            return "angry", intensity

        # ── SARCASTIC ────────────────────────────────────────────────────────
        # Sarcasm emojis OR sarcasm phrases (especially with complaint context)
        sarcasm_emoji_count = len(indicators["sarcasm_emojis"])
        sarcasm_phrase_count = len(indicators["sarcasm_phrases"])
        has_context = indicators["has_complaint_context"]

        if sarcasm_emoji_count >= 1:
            return "sarcastic", 7

        if sarcasm_phrase_count >= 1 and has_context:
            return "sarcastic", 6

        if sarcasm_phrase_count >= 2:
            # Multiple sarcasm phrases even without explicit complaint context
            return "sarcastic", 5

        # ── FRUSTRATED ───────────────────────────────────────────────────────
        frustration_count = len(indicators["frustration_words"])

        if frustration_count >= 2:
            intensity = min(frustration_count * 2 + 3, 9)
            return "frustrated", intensity

        if frustration_count == 1:
            # Single frustration word + repeated punctuation or caps = stronger signal
            if indicators["repeated_punctuation"] or indicators["caps_ratio"] > 0.3:
                return "frustrated", 6
            return "frustrated", 4

        # ── SAD ──────────────────────────────────────────────────────────────
        sad_emoji_count = len(indicators["sad_emojis"])
        if sad_emoji_count >= 1:
            return "sad", min(4 + sad_emoji_count, 8)

        # ── URGENT ───────────────────────────────────────────────────────────
        urgency_count = len(indicators["urgency_words"])
        if urgency_count > 0:
            intensity = min(urgency_count * 2 + 4, 9)
            return "urgent", intensity

        # ── CONFUSED ─────────────────────────────────────────────────────────
        confusion_count = len(indicators["confusion_words"])
        if confusion_count > 0:
            return "confused", 3

        # ── POSITIVE ─────────────────────────────────────────────────────────
        # Only positive if no negative signals at all
        positive_count = len(indicators["positive_words"])
        happy_emoji_count = len(indicators["happy_emojis"])

        if positive_count > 0 or happy_emoji_count > 0:
            return "positive", 2

        return "neutral", 0
