"""
WhatsApp Webhook Handler
FastAPI endpoint for WhatsApp Business API webhooks
Handles: Message reception, verification, brand routing
"""

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Dict, Optional
import os
import hashlib
import hmac

from core.integrations.whatsapp_adapter import WhatsAppMessageAdapter
from core.integrations.whatsapp_formatter import WhatsAppResponseFormatter
from core.orchestrator import ConversationOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="AI CX Agent - WhatsApp Integration",
    description="WhatsApp Business API webhook handler",
    version="1.0.0"
)

# Initialize adapters
adapter = WhatsAppMessageAdapter()
formatter = WhatsAppResponseFormatter()

# Brand phone number mapping
# Maps WhatsApp Business phone numbers to brand IDs
BRAND_PHONE_MAP = {
    "919876543210": "fashionhub",
    "919876543211": "techgear",
    "919876543212": "organicbites"
}

# Verification token (must be set via WHATSAPP_VERIFY_TOKEN environment variable)
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
if not VERIFY_TOKEN:
    import warnings
    warnings.warn(
        "WHATSAPP_VERIFY_TOKEN is not set. WhatsApp webhook verification will fail.",
        RuntimeWarning,
        stacklevel=1,
    )


def get_brand_from_phone(phone_number: str) -> str:
    """
    Determine brand from phone number
    
    Args:
        phone_number: Customer's phone number
    
    Returns:
        Brand ID (defaults to 'fashionhub')
    """
    # In production, you might:
    # 1. Look up customer in database
    # 2. Check which business number they messaged
    # 3. Use conversation history
    
    # For now, default to fashionhub
    return BRAND_PHONE_MAP.get(phone_number, "fashionhub")


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify webhook signature from WhatsApp
    
    Args:
        payload: Request body bytes
        signature: X-Hub-Signature-256 header
    
    Returns:
        True if signature is valid
    """
    app_secret = os.getenv("WHATSAPP_APP_SECRET", "")
    
    if not app_secret:
        # In development, skip verification
        return True
    
    expected_signature = hmac.new(
        app_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]
    
    return hmac.compare_digest(expected_signature, signature)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "WhatsApp Webhook Handler",
        "version": "1.0.0"
    }


@app.get("/webhooks/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """
    Webhook verification endpoint for WhatsApp
    
    WhatsApp sends GET request with:
    - hub.mode: "subscribe"
    - hub.challenge: Random string
    - hub.verify_token: Your verification token
    
    Respond with hub.challenge if token matches
    """
    print(f"📞 Webhook verification request received")
    print(f"   Mode: {hub_mode}")
    print(f"   Token: {hub_verify_token}")
    
    # Verify the token
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("✅ Webhook verified successfully")
        return PlainTextResponse(content=hub_challenge)
    else:
        print("❌ Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    WhatsApp webhook endpoint for incoming messages
    
    Flow:
    1. Receive WhatsApp message
    2. Verify signature (security)
    3. Parse with adapter
    4. Determine brand
    5. Process with orchestrator
    6. Format with formatter
    7. Return response
    """
    try:
        # Get request body
        body = await request.body()
        payload = await request.json()
        
        # Verify signature (in production)
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_webhook_signature(body, signature):
            print("❌ Invalid webhook signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        print(f"📨 WhatsApp webhook received")
        
        # Check if this is a message event
        if payload.get('object') != 'whatsapp_business_account':
            print("⚠️  Not a WhatsApp message event")
            return JSONResponse({"status": "ignored"})
        
        # Check for messages
        entry = payload.get('entry', [])
        if not entry:
            print("⚠️  No entry in payload")
            return JSONResponse({"status": "no_entry"})
        
        # Parse incoming message
        parsed = adapter.parse_incoming_message(payload)
        
        if not parsed['user_message']:
            print("⚠️  Empty message")
            return JSONResponse({"status": "empty_message"})
        
        print(f"📝 Message from {parsed['user_id']}: {parsed['user_message'][:50]}...")
        
        # Determine brand
        # In production, this would check which business number received the message
        brand_id = get_brand_from_phone(parsed['user_id'])
        print(f"🏢 Routing to brand: {brand_id}")
        
        # Process with agent
        orch = ConversationOrchestrator(brand_id=brand_id)
        response, metadata = orch.process_message(parsed['user_message'])
        
        print(f"🤖 Agent response: {response[:50]}...")
        print(f"📊 Quality: {metadata.get('quality_score', {}).get('overall', 0)}/10")
        
        # Format for WhatsApp
        formatted = formatter.format_response(response, {
            'scenario': metadata.get('scenario'),
            'order_data': metadata.get('order_data'),
            'escalation': metadata.get('escalation')
        })
        
        # Convert to WhatsApp API format
        whatsapp_payload = formatter.format_for_whatsapp_api(
            formatted,
            recipient_phone=parsed['user_id']
        )
        
        print(f"✅ Response formatted for WhatsApp")
        
        # In production, you would send this to WhatsApp API
        # For now, return it (WhatsApp webhook doesn't expect response body)
        
        return JSONResponse({
            "status": "success",
            "message_processed": True,
            "response_preview": response[:100],
            "quality_score": metadata.get('quality_score', {}).get('overall'),
            "note": "In production, this would be sent via WhatsApp API"
        })
    
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        
        # Return 200 to acknowledge receipt (prevent retries)
        # But log the error
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "note": "Error logged, returning 200 to prevent retries"
        })


@app.post("/webhooks/whatsapp/send")
async def send_whatsapp_message(
    phone_number: str,
    message: str,
    brand_id: str = "fashionhub"
):
    """
    Manual endpoint to send WhatsApp message
    (For testing purposes)
    
    Args:
        phone_number: Recipient phone number
        message: Message text
        brand_id: Brand identifier
    """
    # Format message
    formatted = formatter.format_response(message, {'scenario': 'general_query'})
    
    # Convert to API format
    whatsapp_payload = formatter.format_for_whatsapp_api(
        formatted,
        recipient_phone=phone_number
    )
    
    return {
        "status": "formatted",
        "payload": whatsapp_payload,
        "note": "In production, this would call WhatsApp API"
    }


@app.get("/webhooks/whatsapp/stats")
async def get_stats():
    """Get webhook statistics"""
    return {
        "adapter": {
            "active_sessions": len(adapter.session_manager),
            "cached_media": len(adapter.media_cache)
        },
        "formatter": formatter.get_stats()
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting WhatsApp Webhook Server")
    print("=" * 70)
    print(f"Verification Token: {VERIFY_TOKEN}")
    print(f"Endpoints:")
    print(f"  - GET  /webhooks/whatsapp (verification)")
    print(f"  - POST /webhooks/whatsapp (messages)")
    print(f"  - GET  /webhooks/whatsapp/stats (statistics)")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
