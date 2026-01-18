from openai import OpenAI
from config import OPENAI_API_KEY
from prompts import SYSTEM_PROMPT
from tools import get_order_status
from intent import detect_intent
import re

client = OpenAI(api_key=OPENAI_API_KEY)

def call_llm(message: str) -> str:
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
    # Handles: 12345, order12345, order 12345, #12345
    match = re.search(r"(?:order\s*#?|#)?(\d{4,6})", text.lower())
    return match.group(1) if match else None


def escalate():
    print("\nAI Agent: I’m forwarding this to our support team so they can assist you further.")


print("\nAI Agent: Hello! How can I assist you today?")

pending_intent = None

print("\nAI Agent: Hello! How can I assist you today?")

while True:
    user_input = input("\nCustomer: ").strip()

    if user_input.lower() in {"exit", "quit"}:
        print("\nAI Agent: Thank you for contacting us. Have a great day!")
        break

    # 🔒 PRIORITY: if waiting for order number
    if pending_intent == "order_status":
        order_id = extract_order_id(user_input)

        if not order_id:
            print("\nAI Agent: Please share a valid order number (for example: 12345).")
            continue

        order_data = get_order_status(order_id)

        if not order_data:
            print("\nAI Agent: I couldn’t find this order. I’m forwarding this to our support team.")
            pending_intent = None
            continue

        print("\nAI Agent:")
        print(f"Your order {order_id} is currently {order_data['status']}.")

        if order_data.get("courier"):
            print(f"Courier: {order_data['courier']}")

        if order_data.get("tracking_url"):
            print(f"Tracking Link: {order_data['tracking_url']}")

        if order_data.get("estimated_delivery"):
            print(f"Estimated Delivery: {order_data['estimated_delivery']}")

        pending_intent = None
        continue

    # 🔹 FIRST-TIME ORDER QUERY (NO LLM)
    if "order" in user_input.lower():
        print("\nAI Agent: Please share your order number so I can check the status.")
        pending_intent = "order_status"
        continue

    # 🤖 ONLY NOW allow LLM
    reply = call_llm(user_input)
    print("\nAI Agent:", reply)

