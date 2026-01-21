# main.py - VERIFIED WORKING VERSION
from openai import OpenAI
from config import OPENAI_API_KEY
from prompts import SYSTEM_PROMPT
from tools import get_order_status
from intent import detect_intent
from conversation_context import ConversationContext
from context_aware_intent import ContextAwareIntentResolver
import re

client = OpenAI(api_key=OPENAI_API_KEY)
context = ConversationContext()
intent_resolver = ContextAwareIntentResolver()

def call_llm(message: str) -> str:
    """Call LLM for general queries only"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content

def extract_order_id(text: str):
    """Handles: 12345, order12345, order 12345, #12345, order#12345"""
    match = re.search(r"(?:order\s*#?|#)?(\d{4,6})\b", text.lower())
    return match.group(1) if match else None

def escalate():
    """Single escalation message"""
    print("\nAI Agent: I'm forwarding this to our support team so they can assist you further.")

def respond_with_order_status(order_id, order_data, is_followup=False):
    """Display order status information"""
    print("\nAI Agent:")
    status = order_data['status'].lower()

    if is_followup:
        if status == "shipped":
            print(f"Your order #{order_id} is on its way! Should reach you by {order_data.get('estimated_delivery', 'soon')}.")
        elif status == "processing":
            print(f"Your order #{order_id} is being prepared. It should ship within 1-2 business days.")
        elif status == "delivered":
            print(f"Good news! Your order #{order_id} was already delivered.")
        else:
            print(f"Your order #{order_id} is currently {order_data['status']}.")
    else:
        if status == "shipped":
            print(f"✓ Your order #{order_id} has been shipped!")
        elif status == "processing":
            print(f"✓ Your order #{order_id} is being prepared.")
        elif status == "delivered":
            print(f"✓ Your order #{order_id} has been delivered!")
        else:
            print(f"✓ Your order #{order_id} status: {order_data['status']}")

    if order_data.get("courier"):
        print(f"  Courier: {order_data['courier']}")
    if order_data.get("tracking_url"):
        print(f"  Track here: {order_data['tracking_url']}")
    if order_data.get("estimated_delivery"):
        print(f"  Expected delivery: {order_data['estimated_delivery']}")
    print("\nAnything else I can help you with?")

def log_context(stage: str):
    """Debug logging"""
    print(f"[DEBUG] {stage}: {context}")

print("\n🤖 AI Customer Support Agent")
print("=" * 50)
print("Type 'exit' or 'quit' to end the conversation.\n")

while True:
    user_input = input("\nCustomer: ").strip()
    
    if not user_input:
        continue
    
    context.store_user_message(user_input)
    
    if user_input.lower() in ["exit", "quit"]:
        print("\nAI Agent: Thank you for contacting us. Have a great day!")
        break
    
    log_context("BEFORE")
    
    # PRIORITY 1: Handle pending order request
    if context.pending_intent == "order_status":
        order_id = extract_order_id(user_input)
        
        if not order_id:
            print("\nAI Agent: Please share a valid order number (for example: 12345).")
            context.store_agent_response("Asked for order number")
            continue
        
        order_data = get_order_status(order_id)
        
        if not order_data:
            print(f"\nAI Agent: I couldn't find order #{order_id}. Could you double-check?")
            context.clear_pending_intent()
            continue
        
        context.update_order_id(order_id)
        context.update_intent("order_status")
        context.clear_pending_intent()
        respond_with_order_status(order_id, order_data)
        log_context("AFTER pending handled")
        continue
    
    # PRIORITY 2: Context-aware intent resolution
    resolved_intent, used_context = intent_resolver.resolve_with_context(user_input, context)
    print(f"[DEBUG] detect_intent returned: '{detect_intent(user_input)}'")
    print(f"[DEBUG] Resolved: '{resolved_intent}', Used context: {used_context}")
    
    # PRIORITY 3: Handle follow-up (BEFORE anything else!)
    if resolved_intent == "order_status_followup":
        order_id = context.last_order_id
        print(f"[DEBUG] Using order from context: {order_id}")
        
        order_data = get_order_status(order_id)
        if not order_data:
            print("\nAI Agent: Having trouble accessing that order. Let me connect you with support.")
            continue
        
        respond_with_order_status(order_id, order_data, is_followup=True)
        log_context("AFTER followup")
        continue
    
    # PRIORITY 4: Handle escalations (only these reset!)
    if resolved_intent == "cancellation":
        escalate()
        context.reset()
        continue
    
    # Update intent
    context.update_intent(resolved_intent)
    
    # PRIORITY 5: Handle new order status
    if resolved_intent == "order_status":
        order_id = extract_order_id(user_input)
        
        if not order_id:
            print("\nAI Agent: Could you please share your order number?")
            context.set_pending_intent("order_status")
            log_context("AFTER asking")
            continue
        
        order_data = get_order_status(order_id)
        
        if not order_data:
            print(f"\nAI Agent: I couldn't find order #{order_id}. Let me forward this to support.")
            continue
        
        context.update_order_id(order_id)
        respond_with_order_status(order_id, order_data)
        log_context("AFTER order_status")
        continue
    
    # PRIORITY 6: Everything else → LLM
    try:
        reply = call_llm(user_input)
        print(f"\nAI Agent: {reply}")
        context.store_agent_response(reply)
        log_context("AFTER LLM")
    except Exception as e:
        print(f"\nAI Agent: I'm having trouble processing that. Could you rephrase?")
        print(f"DEBUG: {e}")