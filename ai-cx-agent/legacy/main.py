# main.py - PRODUCTION HARDENED VERSION
"""
Ecommerce AI Customer Support Agent - Main Conversation Loop
Handles order status queries with context-aware conversation flow.
"""

from openai import OpenAI
from config import OPENAI_API_KEY
from prompts import SYSTEM_PROMPT
from tools import get_order_status
from intent import detect_intent
from conversation_context import ConversationContext
from conversation_state import ActiveTopic
from context_aware_intent import ContextAwareIntentResolver
import re

# Initialize components
client = OpenAI(api_key=OPENAI_API_KEY)
context = ConversationContext()
intent_resolver = ContextAwareIntentResolver()

# Constants
EXIT_COMMANDS = ["exit", "quit", "bye"]
CHECKMARK = "✓"  # Simple checkmark, fallback to > if needed


def call_llm(message: str) -> str:
    """
    Call LLM for general queries only.
    Handles API failures gracefully.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            temperature=0.2,
            max_tokens=300  # Limit response length for support queries
        )
        return response.choices[0].message.content
    except Exception as e:
        # Log error internally but show user-friendly message
        print(f"[SYSTEM ERROR] LLM call failed: {e}")
        return None


def extract_order_id(text: str) -> str:
    """
    Extract order ID from user message.
    Handles: 12345, order12345, order 12345, #12345, order#12345, ORDER 12345
    Returns: order_id as string or None
    """
    # Case-insensitive matching for "order" keyword
    match = re.search(r"(?:order\s*#?|#)?(\d{4,6})\b", text.lower())
    return match.group(1) if match else None


def escalate_to_support():
    """
    Single consistent escalation message.
    Used when agent cannot handle the request.
    """
    print("\nAgent: I'm forwarding this to our support team so they can assist you further.")


def show_order_status(order_id: str, order_data: dict, is_followup: bool = False):
    """
    Display order status information to customer.
    
    Args:
        order_id: The order number
        order_data: Order details from database
        is_followup: Whether this is answering a follow-up question
    """
    print("\nAgent:")
    status = order_data['status'].lower()

    # Choose appropriate phrasing based on context
    if is_followup:
        # Conversational follow-up responses
        if status == "shipped":
            print(f"Your order #{order_id} is on its way! Should reach you by {order_data.get('estimated_delivery', 'soon')}.")
        elif status == "processing":
            print(f"Your order #{order_id} is being prepared. It should ship within 1-2 business days.")
        elif status == "delivered":
            print(f"Good news! Your order #{order_id} was already delivered.")
        else:
            print(f"Your order #{order_id} is currently {order_data['status']}.")
    else:
        # Initial order status responses
        if status == "shipped":
            print(f"{CHECKMARK} Your order #{order_id} has been shipped!")
        elif status == "processing":
            print(f"{CHECKMARK} Your order #{order_id} is being prepared.")
        elif status == "delivered":
            print(f"{CHECKMARK} Your order #{order_id} has been delivered!")
        else:
            print(f"{CHECKMARK} Your order #{order_id} status: {order_data['status']}")

    # Show additional details if available
    if order_data.get("courier"):
        print(f"  Courier: {order_data['courier']}")
    if order_data.get("tracking_url"):
        print(f"  Track here: {order_data['tracking_url']}")
    if order_data.get("estimated_delivery"):
        print(f"  Expected delivery: {order_data['estimated_delivery']}")
    
    print("\nAnything else I can help you with?")


def handle_pending_order_request(user_input: str) -> bool:
    """
    Handle case where we previously asked for order number.
    Returns: True if handled, False otherwise
    """
    if context.pending_intent != "order_status":
        return False
    
    order_id = extract_order_id(user_input)
    
    if not order_id:
        print("\nAgent: Please share a valid order number (for example: 12345).")
        context.store_agent_response("Requested order number again")
        return True
    
    order_data = get_order_status(order_id)
    
    if not order_data:
        # Invalid order - clear pending state and order context
        print(f"\nAgent: I couldn't find order #{order_id}. Could you double-check the number?")
        context.clear_pending_intent()
        context.clear_order_context()  # FIX: Clear invalid order from context
        return True
    
    # Success - update context and show status
    context.update_order_id(order_id)
    context.update_intent("order_status")
    context.clear_pending_intent()
    show_order_status(order_id, order_data)
    
    return True


def handle_followup_question(user_input: str) -> bool:
    """
    Handle follow-up questions about current order in context.
    Returns: True if handled, False otherwise
    """
    # Check if this is a repeated identical question
    if context.is_repeated_query(user_input):
        print("\nAgent: I just shared that information above. Is there something specific you'd like to know more about?")
        return True
    
    order_id = context.last_order_id
    order_data = get_order_status(order_id)
    
    if not order_data:
        # Order data became unavailable
        print("\nAgent: I'm having trouble accessing that order right now. Let me connect you with support.")
        escalate_to_support()
        context.clear_order_context()
        return True
    
    show_order_status(order_id, order_data, is_followup=True)
    return True


def handle_new_order_query(user_input: str) -> bool:
    """
    Handle new order status request.
    Returns: True if handled, False otherwise
    """
    order_id = extract_order_id(user_input)
    
    if not order_id:
        # Need to ask for order number
        print("\nAgent: Could you please share your order number?")
        context.set_pending_intent("order_status")
        return True
    
    order_data = get_order_status(order_id)
    
    if not order_data:
        # Invalid order number provided
        print(f"\nAgent: I couldn't find order #{order_id}. Let me forward this to support.")
        escalate_to_support()
        context.clear_order_context()  # FIX: Clear invalid order
        return True
    
    # Success - show order status
    context.update_order_id(order_id)
    show_order_status(order_id, order_data)
    
    return True


def handle_general_query(user_input: str):
    """
    Handle general queries using LLM.
    Falls back to escalation if LLM fails.
    """
    try:
        reply = call_llm(user_input)
        
        if reply is None:
            # LLM call failed
            print("\nAgent: I'm having trouble processing that right now. Let me connect you with support.")
            escalate_to_support()
        else:
            print(f"\nAgent: {reply}")
            context.store_agent_response(reply)
            
    except Exception as e:
        # Unexpected error
        print("\nAgent: I'm having trouble processing that. Let me connect you with support.")
        escalate_to_support()


def main():
    """Main conversation loop"""
    print("\n🤖 AI Customer Support Agent")
    print("=" * 50)
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        user_input = input("\nCustomer: ").strip()
        
        # Skip empty input
        if not user_input:
            continue
        
        # Store user message and increment turn counter
        context.store_user_message(user_input)
        
        # Check for exit command
        if user_input.lower() in EXIT_COMMANDS:
            print("\nAgent: Thank you for contacting us. Have a great day!")
            break
        
        # PRIORITY 1: Handle pending order number request
        if handle_pending_order_request(user_input):
            continue
        
        # PRIORITY 2: Resolve intent with context awareness
        resolved_intent, used_context = intent_resolver.resolve_with_context(user_input, context)
        
        # PRIORITY 3: Handle follow-up questions (context-aware)
        if resolved_intent == "order_status_followup":
            context.update_intent("order_status_followup")
            handle_followup_question(user_input)
            continue
        
        # PRIORITY 4: Handle escalation intents (these reset context)
        if resolved_intent == "cancellation":
            escalate_to_support()
            context.reset()  # Full reset after cancellation
            continue
        
        # Update current intent
        context.update_intent(resolved_intent)
        
        # PRIORITY 5: Handle new order status queries
        if resolved_intent == "order_status":
            handle_new_order_query(user_input)
            continue
        
        # PRIORITY 6: All other intents → LLM or specific handlers
        if resolved_intent == "returns":
            # Returns policy - use LLM with system prompt
            handle_general_query(user_input)
        elif resolved_intent == "greeting":
            # Simple greeting response
            print("\nAgent: Hello! How can I help you today?")
        else:
            # General query - use LLM
            handle_general_query(user_input)


if __name__ == "__main__":
    main()

