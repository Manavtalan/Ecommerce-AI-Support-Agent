# WhatsApp Webhook Deployment Guide

## Overview
This webhook handler connects your AI CX Agent to WhatsApp Business API.

## Prerequisites
1. WhatsApp Business API access
2. Public URL for webhook (HTTPS required)
3. Verification token
4. App secret (for signature verification)

## Setup Steps

### 1. Set Environment Variables
```bash
export WHATSAPP_VERIFY_TOKEN="your_secure_token_here"
export WHATSAPP_APP_SECRET="your_app_secret_here"
export OPENAI_API_KEY="sk-..."
```

### 2. Run the Server
```bash
# Development
python3 api/webhooks/whatsapp.py

# Production (with gunicorn)
gunicorn api.webhooks.whatsapp:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 3. Expose to Internet
```bash
# Option 1: ngrok (for testing)
ngrok http 8000

# Option 2: Deploy to Railway/Render/Vercel
# See deployment guides

# Option 3: Your own server with HTTPS
```

### 4. Register Webhook with WhatsApp

In Meta Developer Console:
1. Go to WhatsApp > Configuration
2. Set Callback URL: `https://your-domain.com/webhooks/whatsapp`
3. Set Verify Token: (same as WHATSAPP_VERIFY_TOKEN)
4. Subscribe to: `messages` event
5. Click "Verify and Save"

### 5. Test
Send a message to your WhatsApp Business number!

## Endpoints

### GET /webhooks/whatsapp
**Purpose:** Webhook verification  
**Called by:** WhatsApp (during setup)  
**Response:** Returns challenge token if verification succeeds

### POST /webhooks/whatsapp
**Purpose:** Receive incoming messages  
**Called by:** WhatsApp (when customer sends message)  
**Process:**
1. Parse WhatsApp payload
2. Determine brand
3. Process with AI agent
4. Format response
5. Send back to customer

### GET /webhooks/whatsapp/stats
**Purpose:** Monitor webhook health  
**Returns:** Active sessions, message counts, statistics

## Brand Routing

Messages are routed to brands based on:
- Phone number mapping (see BRAND_PHONE_MAP)
- Customer database lookup (custom logic)
- Business account identifier

Update `get_brand_from_phone()` with your routing logic.

## Security

### Signature Verification
All POST requests are verified using `X-Hub-Signature-256` header.
```python
def verify_webhook_signature(payload, signature):
    # Uses WHATSAPP_APP_SECRET to verify
    pass
```

### HTTPS Required
WhatsApp only sends webhooks to HTTPS URLs.

## Monitoring

Check webhook health:
```bash
curl https://your-domain.com/webhooks/whatsapp/stats
```

## Troubleshooting

### Verification Fails
- Check WHATSAPP_VERIFY_TOKEN matches Meta console
- Ensure endpoint is publicly accessible
- Check server logs

### Messages Not Received
- Verify webhook is registered in Meta console
- Check signature verification (WHATSAPP_APP_SECRET)
- Review server logs for errors

### Responses Not Sent
- Implement actual WhatsApp API call (currently mocked)
- Use official WhatsApp Business API client
- Check API credentials

## Production Checklist
- [ ] HTTPS enabled
- [ ] Environment variables set
- [ ] Signature verification enabled
- [ ] Error logging configured
- [ ] Rate limiting implemented
- [ ] Webhook registered with WhatsApp
- [ ] Brand routing configured
- [ ] Tested end-to-end

## Next Steps
1. Implement actual WhatsApp API sending
2. Add webhook retry logic
3. Implement message queuing
4. Add monitoring/alerting
5. Load testing
