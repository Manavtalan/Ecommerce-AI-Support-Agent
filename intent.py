# intent.py - COPY THIS EXACTLY

import re

def detect_intent(message: str) -> str:
    """
    Detect user intent from message.
    Priority order matters!
    """
    msg = message.lower().strip()
    
    # PRIORITY 1: Cancellation (HIGHEST)
    cancellation_keywords = [
        "cancel my order", "cancel order", "i want to cancel",
        "please cancel", "cancel this order", "cancel it"
    ]
    if any(keyword in msg for keyword in cancellation_keywords):
        return "cancellation"
    
    # PRIORITY 2: Order Status (BEFORE GREETING!)
    has_order_number = bool(re.search(r'\b\d{4,6}\b', msg))
    
    order_keywords = [
        "order", "tracking", "track", "status", 
        "where is", "shipped", "delivery", "deliver",
        "package", "shipment", "eta", "arrive", "receive"
    ]
    
    # If message contains order-related content
    if has_order_number or any(keyword in msg for keyword in order_keywords):
        return "order_status"
    
    # Check if it's JUST a number (like "67890")
    if re.fullmatch(r'\d{4,6}', msg):
        return "order_status"
    
    # PRIORITY 3: Returns/Refunds
    return_keywords = ["return", "refund", "money back"]
    if any(keyword in msg for keyword in return_keywords):
        return "returns"
    
    # PRIORITY 4: Greeting (AFTER order detection!)
    greeting_keywords = ["hello", "hi", "hey", "good morning", "good afternoon"]
    for keyword in greeting_keywords:
        if msg.startswith(keyword):
            rest = msg.replace(keyword, "").strip()
            if len(rest) < 5:  # Short = just greeting
                return "greeting"
            # Has more content after greeting, continue checking
    
    # DEFAULT: General
    return "general"