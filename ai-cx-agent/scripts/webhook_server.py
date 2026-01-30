"""
Shopify Webhook Server
Receives and processes Shopify webhooks
"""

import os
import hmac
import hashlib
import json
from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional
from dotenv import load_dotenv
from core.integrations.shopify.sync import ShopifyOrderSync

load_dotenv()

app = FastAPI(title="Shopify Webhook Server")

# Initialize order sync
order_sync = ShopifyOrderSync()

# Webhook secret for verification
WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")


def verify_webhook(data: bytes, hmac_header: str) -> bool:
    """
    Verify Shopify webhook signature
    
    Args:
        data: Raw request body
        hmac_header: X-Shopify-Hmac-SHA256 header
    
    Returns:
        True if valid
    """
    if not WEBHOOK_SECRET:
        print("⚠️  Warning: No webhook secret configured")
        return True  # Allow in development
    
    # Calculate expected HMAC
    hash = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        data,
        hashlib.sha256
    )
    expected_hmac = hash.hexdigest()
    
    return hmac.compare_digest(expected_hmac, hmac_header)


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "service": "Shopify Webhook Server"}


@app.post("/webhooks/shopify/orders/create")
async def order_created(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None)
):
    """Handle order creation webhook"""
    # Get raw body
    body = await request.body()
    
    # Verify signature
    if x_shopify_hmac_sha256:
        if not verify_webhook(body, x_shopify_hmac_sha256):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse order data
    order_data = json.loads(body)
    
    print(f"📦 New order created: #{order_data.get('order_number')}")
    
    # Sync this order
    order_id = str(order_data.get('order_number'))
    order_sync.get_order(order_id, force_refresh=True)
    
    return {"status": "processed", "order": order_id}


@app.post("/webhooks/shopify/orders/update")
async def order_updated(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None)
):
    """Handle order update webhook"""
    # Get raw body
    body = await request.body()
    
    # Verify signature
    if x_shopify_hmac_sha256:
        if not verify_webhook(body, x_shopify_hmac_sha256):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse order data
    order_data = json.loads(body)
    
    print(f"🔄 Order updated: #{order_data.get('order_number')}")
    print(f"   Status: {order_data.get('fulfillment_status')}")
    
    # Refresh this order
    order_id = str(order_data.get('order_number'))
    order_sync.get_order(order_id, force_refresh=True)
    
    return {"status": "processed", "order": order_id}


@app.post("/webhooks/shopify/fulfillments/create")
async def fulfillment_created(
    request: Request,
    x_shopify_hmac_sha256: Optional[str] = Header(None)
):
    """Handle fulfillment creation (shipping) webhook"""
    # Get raw body
    body = await request.body()
    
    # Verify signature
    if x_shopify_hmac_sha256:
        if not verify_webhook(body, x_shopify_hmac_sha256):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse data
    fulfillment_data = json.loads(body)
    
    print(f"🚚 Order shipped: #{fulfillment_data.get('order_number')}")
    print(f"   Tracking: {fulfillment_data.get('tracking_number')}")
    
    return {"status": "processed"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Shopify Webhook Server...")
    print("   Listening on http://localhost:8000")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000)
