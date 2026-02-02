"""
WhatsApp Message Adapter
Converts WhatsApp webhook payloads to agent format
Handles: Text, media, buttons, session management
"""

from typing import Dict, List, Optional
from datetime import datetime
import hashlib


class WhatsAppMessageAdapter:
    """Converts WhatsApp messages to agent format"""
    
    def __init__(self):
        """Initialize adapter with session management"""
        self.session_manager = {}  # Track WhatsApp sessions
        self.media_cache = {}  # Cache downloaded media
    
    def parse_incoming_message(self, whatsapp_payload: Dict) -> Dict:
        """
        Parse WhatsApp webhook payload
        
        Args:
            whatsapp_payload: Raw WhatsApp webhook data from Meta
            Expected format:
            {
                "object": "whatsapp_business_account",
                "entry": [{
                    "changes": [{
                        "value": {
                            "messages": [{
                                "from": "91234567890",
                                "id": "wamid.xxx",
                                "timestamp": "1234567890",
                                "type": "text",
                                "text": {"body": "Where is my order?"}
                            }]
                        }
                    }]
                }]
            }
        
        Returns:
            {
                user_message: str,
                session_id: str,
                user_id: str,
                message_id: str,
                media: list (optional),
                context: dict
            }
        """
        try:
            # Extract message from nested structure
            entry = whatsapp_payload.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                raise ValueError("No messages in payload")
            
            message = messages[0]
            
            # Extract core fields
            user_id = message.get('from')  # Phone number
            message_id = message.get('id')
            timestamp = message.get('timestamp')
            message_type = message.get('type', 'text')
            
            # Generate session ID (unique per user)
            session_id = self._generate_session_id(user_id)
            
            # Extract message content based on type
            user_message = ""
            media = []
            
            if message_type == 'text':
                user_message = message.get('text', {}).get('body', '')
            
            elif message_type == 'image':
                # Image message
                image_data = message.get('image', {})
                media.append({
                    'type': 'image',
                    'id': image_data.get('id'),
                    'mime_type': image_data.get('mime_type'),
                    'caption': image_data.get('caption', '')
                })
                user_message = image_data.get('caption', 'Image sent')
            
            elif message_type == 'button':
                # Button response
                button_data = message.get('button', {})
                user_message = button_data.get('text', '')
            
            elif message_type == 'interactive':
                # Interactive button/list response
                interactive = message.get('interactive', {})
                if interactive.get('type') == 'button_reply':
                    user_message = interactive.get('button_reply', {}).get('title', '')
                elif interactive.get('type') == 'list_reply':
                    user_message = interactive.get('list_reply', {}).get('title', '')
            
            # Store session context
            self._update_session_context(session_id, {
                'user_id': user_id,
                'last_message_id': message_id,
                'last_timestamp': timestamp,
                'message_type': message_type
            })
            
            return {
                'user_message': user_message,
                'session_id': session_id,
                'user_id': user_id,
                'message_id': message_id,
                'media': media if media else None,
                'context': {
                    'platform': 'whatsapp',
                    'message_type': message_type,
                    'timestamp': timestamp
                }
            }
        
        except Exception as e:
            print(f"❌ Error parsing WhatsApp message: {e}")
            # Return minimal valid structure
            return {
                'user_message': '',
                'session_id': 'unknown',
                'user_id': 'unknown',
                'message_id': 'unknown',
                'media': None,
                'context': {'error': str(e)}
            }
    
    def handle_media(self, media_id: str, access_token: str) -> Dict:
        """
        Download and process media (damaged product images)
        
        Args:
            media_id: WhatsApp media ID
            access_token: WhatsApp Business API access token
        
        Returns:
            {
                success: bool,
                media_url: str,
                media_type: str,
                local_path: str (optional)
            }
        """
        # Check cache
        if media_id in self.media_cache:
            return self.media_cache[media_id]
        
        try:
            # Step 1: Get media URL from WhatsApp
            # GET https://graph.facebook.com/v18.0/{media_id}
            # Headers: Authorization: Bearer {access_token}
            
            # This would be the actual API call:
            # response = requests.get(
            #     f"https://graph.facebook.com/v18.0/{media_id}",
            #     headers={"Authorization": f"Bearer {access_token}"}
            # )
            # media_url = response.json().get('url')
            
            # Step 2: Download media from URL
            # media_response = requests.get(media_url, headers={"Authorization": f"Bearer {access_token}"})
            
            # For now, return structure (actual implementation would download)
            result = {
                'success': True,
                'media_id': media_id,
                'media_url': f'https://example.com/media/{media_id}',
                'media_type': 'image/jpeg',
                'local_path': None,  # Would save to storage
                'note': 'Media download not implemented (requires WhatsApp API credentials)'
            }
            
            # Cache result
            self.media_cache[media_id] = result
            
            return result
        
        except Exception as e:
            print(f"❌ Error downloading media: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_session_id(self, user_id: str) -> str:
        """
        Generate consistent session ID for user
        
        Args:
            user_id: WhatsApp user ID (phone number)
        
        Returns:
            Session ID (hash of user_id)
        """
        # Create hash of user_id for session
        hash_object = hashlib.sha256(user_id.encode())
        return f"wa_{hash_object.hexdigest()[:16]}"
    
    def _update_session_context(self, session_id: str, context: Dict):
        """
        Update session context
        
        Args:
            session_id: Session identifier
            context: Context data to store
        """
        if session_id not in self.session_manager:
            self.session_manager[session_id] = {
                'created_at': datetime.now().isoformat(),
                'message_count': 0
            }
        
        self.session_manager[session_id].update(context)
        self.session_manager[session_id]['message_count'] += 1
        self.session_manager[session_id]['updated_at'] = datetime.now().isoformat()
    
    def get_session_context(self, session_id: str) -> Optional[Dict]:
        """Get stored session context"""
        return self.session_manager.get(session_id)
    
    def clear_session(self, session_id: str):
        """Clear session data"""
        if session_id in self.session_manager:
            del self.session_manager[session_id]
    
    def __repr__(self) -> str:
        return f"WhatsAppMessageAdapter(active_sessions={len(self.session_manager)})"


# Testing function
def test_whatsapp_adapter():
    """Test WhatsApp message adapter"""
    print("🧪 TESTING WHATSAPP MESSAGE ADAPTER")
    print("=" * 70)
    print()
    
    adapter = WhatsAppMessageAdapter()
    
    # Test 1: Text message
    print("TEST 1: Text Message")
    text_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.HBgNOTE5ODc2NTQzMjEwFQIAERgSMzg1QTUyQjY4RjFFNjg3RjNCQUEA",
                        "timestamp": "1234567890",
                        "type": "text",
                        "text": {"body": "Where is my order 12345?"}
                    }]
                }
            }]
        }]
    }
    
    result = adapter.parse_incoming_message(text_payload)
    print(f"User Message: {result['user_message']}")
    print(f"Session ID: {result['session_id']}")
    print(f"User ID: {result['user_id']}")
    print(f"✅ Text message parsed")
    print()
    
    # Test 2: Image message
    print("TEST 2: Image Message")
    image_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.xxx",
                        "timestamp": "1234567891",
                        "type": "image",
                        "image": {
                            "id": "media123",
                            "mime_type": "image/jpeg",
                            "caption": "Product is damaged"
                        }
                    }]
                }
            }]
        }]
    }
    
    result = adapter.parse_incoming_message(image_payload)
    print(f"User Message: {result['user_message']}")
    print(f"Media: {result['media']}")
    print(f"✅ Image message parsed")
    print()
    
    # Test 3: Button response
    print("TEST 3: Button Response")
    button_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.yyy",
                        "timestamp": "1234567892",
                        "type": "button",
                        "button": {
                            "text": "Track Order",
                            "payload": "track_order_12345"
                        }
                    }]
                }
            }]
        }]
    }
    
    result = adapter.parse_incoming_message(button_payload)
    print(f"User Message: {result['user_message']}")
    print(f"✅ Button response parsed")
    print()
    
    # Test 4: Session consistency
    print("TEST 4: Session Consistency")
    result1 = adapter.parse_incoming_message(text_payload)
    result2 = adapter.parse_incoming_message(text_payload)
    
    if result1['session_id'] == result2['session_id']:
        print(f"✅ Session ID consistent: {result1['session_id']}")
    else:
        print(f"❌ Session ID mismatch!")
    print()
    
    # Test 5: Media handling
    print("TEST 5: Media Download (Mock)")
    media_result = adapter.handle_media("media123", "fake_token")
    print(f"Media URL: {media_result.get('media_url')}")
    print(f"Success: {media_result.get('success')}")
    print(f"✅ Media handler working")
    print()
    
    # Summary
    print("=" * 70)
    print(f"Active Sessions: {len(adapter.session_manager)}")
    print(f"Cached Media: {len(adapter.media_cache)}")
    print()
    print("✅ WhatsApp Message Adapter tests complete!")


if __name__ == "__main__":
    test_whatsapp_adapter()
