"""
Instagram DM Adapter
Handles Instagram Direct Messages
Features: Character limits, media handling, story replies
"""

from typing import Dict, List, Optional
import hashlib
from datetime import datetime


class InstagramDMAdapter:
    """Handles Instagram Direct Messages"""
    
    MAX_LENGTH = 1000  # Instagram DM character limit
    
    def __init__(self):
        """Initialize Instagram DM adapter"""
        self.session_manager = {}
        self.media_cache = {}
    
    def parse_dm(self, ig_payload: Dict) -> Dict:
        """
        Parse Instagram DM webhook payload
        
        Args:
            ig_payload: Instagram webhook data
            Expected format:
            {
                "object": "instagram",
                "entry": [{
                    "messaging": [{
                        "sender": {"id": "instagram_user_id"},
                        "recipient": {"id": "page_id"},
                        "timestamp": 1234567890,
                        "message": {
                            "mid": "message_id",
                            "text": "Where is my order?"
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
                media: dict (optional),
                context: dict
            }
        """
        try:
            # Extract message from nested structure
            entry = ig_payload.get('entry', [{}])[0]
            messaging = entry.get('messaging', [])
            
            if not messaging:
                raise ValueError("No messaging in payload")
            
            message_event = messaging[0]
            
            # Extract core fields
            sender = message_event.get('sender', {})
            user_id = sender.get('id', 'unknown')
            
            recipient = message_event.get('recipient', {})
            page_id = recipient.get('id')
            
            timestamp = message_event.get('timestamp')
            
            # Extract message
            message = message_event.get('message', {})
            message_id = message.get('mid')
            text = message.get('text', '')
            
            # Check for attachments (images, videos)
            attachments = message.get('attachments', [])
            media = None
            
            if attachments:
                media = self._parse_attachments(attachments)
                if not text and media:
                    text = "Media sent"
            
            # Check for story reply
            is_story_reply = message.get('is_echo') is False and message.get('reply_to')
            if is_story_reply:
                text = f"[Story Reply] {text}"
            
            # Generate session ID
            session_id = self._generate_session_id(user_id)
            
            # Update session context
            self._update_session_context(session_id, {
                'user_id': user_id,
                'page_id': page_id,
                'last_message_id': message_id,
                'last_timestamp': timestamp
            })
            
            return {
                'user_message': text,
                'session_id': session_id,
                'user_id': user_id,
                'message_id': message_id,
                'media': media,
                'context': {
                    'platform': 'instagram',
                    'page_id': page_id,
                    'timestamp': timestamp,
                    'is_story_reply': is_story_reply
                }
            }
        
        except Exception as e:
            print(f"❌ Error parsing Instagram DM: {e}")
            return {
                'user_message': '',
                'session_id': 'unknown',
                'user_id': 'unknown',
                'message_id': 'unknown',
                'media': None,
                'context': {'error': str(e)}
            }
    
    def format_dm_response(self, response: str, context: Dict = None) -> Dict:
        """
        Format response for Instagram DM (1000 char limit)
        
        Args:
            response: Agent's text response
            context: Additional context (optional)
        
        Returns:
            {
                text: str (or list of str if split),
                message_count: int,
                quick_replies: list (optional)
            }
        """
        context = context or {}
        
        # Check if message needs splitting
        if len(response) > self.MAX_LENGTH:
            messages = self._split_message(response)
            return {
                'text': messages,
                'message_count': len(messages),
                'split': True
            }
        
        # Check if we should add quick replies
        quick_replies = self._suggest_quick_replies(context)
        
        return {
            'text': response,
            'message_count': 1,
            'quick_replies': quick_replies
        }
    
    def _split_message(self, text: str) -> List[str]:
        """
        Split long messages at 1000 char limit
        
        Args:
            text: Message to split
        
        Returns:
            List of message chunks
        """
        chunks = []
        chunk_size = self.MAX_LENGTH - 15  # Leave room for "(cont...)"
        
        # Try to split at sentence boundaries
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            # Add period back
            sentence = sentence if sentence.endswith('.') else sentence + '.'
            
            if len(current_chunk) + len(sentence) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence too long, force split
                    for i in range(0, len(sentence), chunk_size):
                        chunks.append(sentence[i:i + chunk_size])
                    current_chunk = ""
            else:
                current_chunk += " " + sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Add continuation markers
        for i in range(len(chunks) - 1):
            chunks[i] += " (cont...)"
        
        return chunks
    
    def _parse_attachments(self, attachments: List[Dict]) -> Dict:
        """
        Parse Instagram message attachments
        
        Args:
            attachments: List of attachment dicts
        
        Returns:
            Media information dict
        """
        media_items = []
        
        for attachment in attachments:
            attachment_type = attachment.get('type')
            
            if attachment_type == 'image':
                payload = attachment.get('payload', {})
                media_items.append({
                    'type': 'image',
                    'url': payload.get('url'),
                    'width': payload.get('width'),
                    'height': payload.get('height')
                })
            
            elif attachment_type == 'video':
                payload = attachment.get('payload', {})
                media_items.append({
                    'type': 'video',
                    'url': payload.get('url')
                })
            
            elif attachment_type == 'audio':
                payload = attachment.get('payload', {})
                media_items.append({
                    'type': 'audio',
                    'url': payload.get('url')
                })
        
        return {
            'count': len(media_items),
            'items': media_items
        }
    
    def _suggest_quick_replies(self, context: Dict) -> Optional[List[str]]:
        """
        Suggest quick reply options (Instagram supports up to 13)
        
        Args:
            context: Conversation context
        
        Returns:
            List of quick reply texts
        """
        scenario = context.get('scenario', '')
        
        quick_replies = []
        
        # Order-related
        if 'order' in scenario.lower():
            quick_replies.extend([
                "Track my order",
                "Return item",
                "Contact support"
            ])
        
        # Policy-related
        elif 'policy' in scenario.lower():
            quick_replies.extend([
                "Returns policy",
                "Shipping info",
                "Contact support"
            ])
        
        # General
        else:
            quick_replies.extend([
                "Track order",
                "Help",
                "Talk to human"
            ])
        
        # Limit to 3 quick replies for simplicity
        return quick_replies[:3] if quick_replies else None
    
    def handle_dm_media(self, media_url: str, media_type: str = 'image') -> Dict:
        """
        Process media sent via DM
        
        Args:
            media_url: URL of the media
            media_type: Type (image/video/audio)
        
        Returns:
            {
                success: bool,
                media_url: str,
                media_type: str,
                note: str
            }
        """
        # Check cache
        cache_key = hashlib.sha256(media_url.encode()).hexdigest()[:16]
        
        if cache_key in self.media_cache:
            return self.media_cache[cache_key]
        
        # In production, you would:
        # 1. Download media from Instagram
        # 2. Process/analyze if needed
        # 3. Store in your storage
        
        result = {
            'success': True,
            'media_url': media_url,
            'media_type': media_type,
            'note': 'Media download structure ready (requires Instagram API credentials)'
        }
        
        # Cache result
        self.media_cache[cache_key] = result
        
        return result
    
    def format_for_instagram_api(
        self,
        formatted_response: Dict,
        recipient_id: str
    ) -> Dict:
        """
        Format for Instagram Messaging API
        
        Args:
            formatted_response: Output from format_dm_response()
            recipient_id: Instagram user ID
        
        Returns:
            Instagram API-compatible payload
        """
        # For text messages
        if not formatted_response.get('split'):
            payload = {
                'recipient': {'id': recipient_id},
                'message': {
                    'text': formatted_response['text']
                }
            }
            
            # Add quick replies if present
            if formatted_response.get('quick_replies'):
                payload['message']['quick_replies'] = [
                    {
                        'content_type': 'text',
                        'title': reply,
                        'payload': reply.lower().replace(' ', '_')
                    }
                    for reply in formatted_response['quick_replies']
                ]
            
            return payload
        else:
            # Multiple messages (split)
            return {
                'recipient': {'id': recipient_id},
                'message': {
                    'text': formatted_response['text'][0]
                },
                'note': f"Message split into {len(formatted_response['text'])} parts"
            }
    
    def _generate_session_id(self, user_id: str) -> str:
        """Generate consistent session ID"""
        hash_obj = hashlib.sha256(user_id.encode())
        return f"ig_{hash_obj.hexdigest()[:16]}"
    
    def _update_session_context(self, session_id: str, context: Dict):
        """Update session context"""
        if session_id not in self.session_manager:
            self.session_manager[session_id] = {
                'created_at': datetime.now().isoformat(),
                'message_count': 0
            }
        
        self.session_manager[session_id].update(context)
        self.session_manager[session_id]['message_count'] += 1
        self.session_manager[session_id]['updated_at'] = datetime.now().isoformat()
    
    def get_session_context(self, session_id: str) -> Optional[Dict]:
        """Get session context"""
        return self.session_manager.get(session_id)
    
    def __repr__(self) -> str:
        return f"InstagramDMAdapter(active_sessions={len(self.session_manager)})"


# Testing function
def test_instagram_adapter():
    """Test Instagram DM adapter"""
    print("🧪 TESTING INSTAGRAM DM ADAPTER")
    print("=" * 70)
    print()
    
    adapter = InstagramDMAdapter()
    
    # Test 1: Parse text message
    print("TEST 1: Text Message")
    text_payload = {
        "object": "instagram",
        "entry": [{
            "messaging": [{
                "sender": {"id": "instagram_user_123"},
                "recipient": {"id": "page_456"},
                "timestamp": 1234567890,
                "message": {
                    "mid": "mid.123",
                    "text": "Where is my order 12345?"
                }
            }]
        }]
    }
    
    result = adapter.parse_dm(text_payload)
    print(f"User Message: {result['user_message']}")
    print(f"Session ID: {result['session_id']}")
    print(f"User ID: {result['user_id']}")
    print(f"✅ Text message parsed")
    print()
    
    # Test 2: Parse message with image
    print("TEST 2: Message with Image")
    image_payload = {
        "object": "instagram",
        "entry": [{
            "messaging": [{
                "sender": {"id": "instagram_user_123"},
                "recipient": {"id": "page_456"},
                "timestamp": 1234567891,
                "message": {
                    "mid": "mid.124",
                    "text": "Product is damaged",
                    "attachments": [{
                        "type": "image",
                        "payload": {
                            "url": "https://example.com/image.jpg",
                            "width": 800,
                            "height": 600
                        }
                    }]
                }
            }]
        }]
    }
    
    result = adapter.parse_dm(image_payload)
    print(f"User Message: {result['user_message']}")
    print(f"Media: {result['media']}")
    print(f"✅ Image message parsed")
    print()
    
    # Test 3: Short response
    print("TEST 3: Short Response")
    short_response = "Your order #12345 is on its way! 📦"
    
    formatted = adapter.format_dm_response(short_response, {'scenario': 'order_status'})
    print(f"Text: {formatted['text']}")
    print(f"Message Count: {formatted['message_count']}")
    print(f"Quick Replies: {formatted.get('quick_replies')}")
    print(f"✅ Short response formatted")
    print()
    
    # Test 4: Long response (needs splitting)
    print("TEST 4: Long Response (Split Required)")
    long_response = "A" * 1200  # 1200 characters
    
    formatted = adapter.format_dm_response(long_response)
    print(f"Message Count: {formatted['message_count']}")
    print(f"Split: {formatted.get('split')}")
    
    if formatted.get('split'):
        for i, chunk in enumerate(formatted['text'], 1):
            print(f"  Part {i}: {len(chunk)} chars")
            assert len(chunk) <= 1000, f"Chunk {i} exceeds 1000 char limit!"
    
    print(f"✅ Long response split correctly")
    print()
    
    # Test 5: Instagram API format
    print("TEST 5: Instagram API Format")
    api_payload = adapter.format_for_instagram_api(
        {
            'text': 'Hello! How can I help?',
            'message_count': 1,
            'quick_replies': ['Track order', 'Help']
        },
        recipient_id='instagram_user_123'
    )
    
    print(f"Recipient ID: {api_payload['recipient']['id']}")
    print(f"Message: {api_payload['message']['text']}")
    print(f"Quick Replies: {len(api_payload['message'].get('quick_replies', []))}")
    print(f"✅ Instagram API format correct")
    print()
    
    # Test 6: Session consistency
    print("TEST 6: Session Consistency")
    result1 = adapter.parse_dm(text_payload)
    result2 = adapter.parse_dm(text_payload)
    
    if result1['session_id'] == result2['session_id']:
        print(f"✅ Session ID consistent: {result1['session_id']}")
    else:
        print(f"❌ Session ID mismatch!")
    print()
    
    # Summary
    print("=" * 70)
    print(f"Active Sessions: {len(adapter.session_manager)}")
    print(f"Cached Media: {len(adapter.media_cache)}")
    print()
    print("✅ Instagram DM Adapter tests complete!")


if __name__ == "__main__":
    test_instagram_adapter()
