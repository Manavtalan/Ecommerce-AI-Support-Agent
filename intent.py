def detect_intent(message: str) -> str:
    msg = message.lower()

    if any(word in msg for word in ["cancel", "cancellation"]):
        return "cancellation"

    if any(word in msg for word in ["refund", "return"]):
        return "returns"

    if any(word in msg for word in ["where", "status", "track"]):
        return "order_status"

    if any(word in msg for word in ["delivery", "shipping"]):
        return "shipping"

    return "general"
