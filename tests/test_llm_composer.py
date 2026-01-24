from llm_composer import LLMResponseComposer

composer = LLMResponseComposer()

response = composer.compose_response(
    scenario="delay_explanation",
    facts={
        "order_id": "12345",
        "status": "shipped",
        "courier": "Delhivery",
        "eta": "2026-01-18",
        "days_since_order": 10
    },
    constraints=["cannot_cancel", "cannot_change_delivery_date"],
    emotion="frustrated"
)

print("\n--- AI RESPONSE ---\n")
print(response)

