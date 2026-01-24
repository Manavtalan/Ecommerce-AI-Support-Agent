# intent.py
"""
Intent Detection Module
Classifies user messages into specific intents for routing.
"""

import re


def detect_intent(message: str) -> str:
    """
    Detect user intent from message using keyword matching.
    
    Priority order (highest to lowest):
    1. Cancellation (requires immediate escalation)
    2. Order Status (most common query)
    3. Returns/Refunds
    4. Greeting (only if standalone)
    5. General (fallback)
    
    Args:
        message: User's input message
        
    Returns:
        Intent string: "cancellation", "order_status", "returns", "greeting", or "general"
    """
    msg = message.lower().strip()
    
    # PRIORITY 1: Cancellation (HIGHEST - requires escalation)
    cancellation_keywords = [
        "cancel my order",
        "cancel order",
        "i want to cancel",
        "please cancel",
        "cancel this order",
        "cancel it"
    ]
    if any(keyword in msg for keyword in cancellation_keywords):
        return "cancellation"
    
    # PRIORITY 2: Order Status (BEFORE GREETING!)
    # Check for explicit order numbers (4-6 digits)
    has_order_number = bool(re.search(r'\b\d{4,6}\b', msg))
    
    order_keywords = [
        "order", "tracking", "track", "status",
        "where is", "shipped", "delivery", "deliver",
        "package", "shipment", "eta", "arrive", "receive"
    ]
    
    # If message contains order-related content OR has an order number
    if has_order_number or any(keyword in msg for keyword in order_keywords):
        return "order_status"
    
    # Check if it's JUST a number (user providing order ID)
    if re.fullmatch(r'\d{4,6}', msg):
        return "order_status"
    
    # PRIORITY 3: Returns/Refunds
    return_keywords = ["return", "refund", "money back", "send back"]
    if any(keyword in msg for keyword in return_keywords):
        return "returns"
    
    # PRIORITY 4: Greeting (AFTER order detection!)
    # Must be at the start and relatively standalone
    greeting_keywords = [
        "hello", "hi ", "hi,", "hey", "hey ", "hey,",
        "good morning", "good afternoon", "good evening"
    ]
    
    for keyword in greeting_keywords:
        # Check if greeting is at start
        if msg.startswith(keyword):
            # Get remaining text after greeting
            rest = msg.replace(keyword, "").strip()
            
            # If very short (just greeting), classify as greeting
            if len(rest) < 5:
                return "greeting"
            
            # If there's substantial content after greeting, keep checking
            # FIX: "hello my order is 12345" should be order_status, not greeting
            # This is handled by re-checking for order keywords in the rest
            if any(kw in rest for kw in order_keywords) or re.search(r'\d{4,6}', rest):
                return "order_status"
    
    # DEFAULT: General query
    return "general"
