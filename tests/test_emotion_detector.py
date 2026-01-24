from emotion_detector import EmotionDetector

test_messages = [
    "Where is my order?",
    "Why is my order so late?",
    "THIS IS RIDICULOUS!!!",
    "Can you explain this to me?",
    "Thanks, that helps a lot!",
    "I need this ASAP",
    "This is the worst service ever",
    "ok"
]

for msg in test_messages:
    emotion, intensity, indicators = EmotionDetector.detect_emotion(msg)
    print("=" * 50)
    print(f"Message: {msg}")
    print(f"Emotion: {emotion}")
    print(f"Intensity: {intensity}")
    print(f"Indicators: {indicators}")

