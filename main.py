from openai import OpenAI
from config import OPENAI_API_KEY
from prompts import SYSTEM_PROMPT
from tools import get_order_status
from intent import detect_intent
import re


client = OpenAI(api_key=OPENAI_API_KEY)

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

print("\n🤖 AI Customer Support Agent")
print("=" * 50)
print("Type 'exit' or 'quit' to end the conversation.\n")


def respond_with_order_status(order_id, order_data):
    print("\nAI Agent:")

    status = order_data['status'].lower()

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

pending_intent = None

while True:
    user_input = input("\nCustomer: ").strip()
    
    if not user_input:
        continue
    
    if user_input.lower() in ["exit", "quit"]:
        print("\nAI Agent: Thank you for contacting us. Have a great day!")
        break
    
    # ========================================
    # PRIORITY 1: Handle pending order request
    # ========================================
    if pending_intent == "order_status":
        order_id = extract_order_id(user_input)
        
        if not order_id:
            print("\nAI Agent: Please share a valid order number (for example: 12345).")
            continue
        
        order_data = get_order_status(order_id)
        
        if not order_data:
            print(f"\nAI Agent: I couldn't find order #{order_id}. Could you double-check the number?")
            pending_intent = None
            continue
        
        # ✅ DIRECT RESPONSE - Clear and professional
        respond_with_order_status(order_id, order_data)

        pending_intent = None
        continue
    
    # ========================================
    # PRIORITY 2: Detect new query intent
    # ========================================
    intent = detect_intent(user_input)
    
    # Block cancellations immediately
    if intent == "cancellation":
        escalate()
        continue
    
    # Handle order status requests
    if intent == "order_status":
        # Check if order number is in the message
        order_id = extract_order_id(user_input)
        
        if not order_id:
            # Ask for order number
            print("\nAI Agent: Could you please share your order number?")
            pending_intent = "order_status"
            continue
        
        # We have the order number, look it up
        order_data = get_order_status(order_id)
        
        if not order_data:
            print(f"\nAI Agent: I couldn't find order #{order_id}. Let me forward this to our support team.")
            continue
        
        # ✅ DIRECT RESPONSE
        respond_with_order_status(order_id, order_data)
        continue
    
    # ========================================
    # PRIORITY 3: Everything else → LLM
    # ========================================
    try:
        reply = call_llm(user_input)
        print("\nAI Agent:", reply)
    except Exception as e:
        print(f"\nAI Agent: I'm having trouble processing that. Could you rephrase?")
        print(f"DEBUG: {e}")