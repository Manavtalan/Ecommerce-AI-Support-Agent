"""
WhatsApp Response Formatter
Converts agent responses to WhatsApp-compatible format
Handles: Character limits, buttons, message splitting
"""

from typing import Dict, List, Optional
import re


class WhatsAppResponseFormatter:
    """Formats agent responses for WhatsApp"""
    
    MAX_LENGTH = 1600  # WhatsApp character limit
    MAX_BUTTONS = 3    # Maximum quick reply buttons
    
    def __init__(self):
        """Initialize formatter"""
        self.formatting_stats = {
            'messages_formatted': 0,
            'messages_split': 0,
            'buttons_added': 0
        }
    
    def format_response(
        self,
        agent_response: str,
        context: Dict
    ) -> Dict:
        """
        Format response for WhatsApp
        
        Args:
            agent_response: Agent's text response
            context: Additional context
                - scenario: str (order_status, policy_question, etc.)
                - order_data: dict (optional)
                - escalation: dict (optional)
                - metadata: dict
        
        Returns:
            {
                text: str (or list of str if split),
                buttons: list (optional),
                type: str (text/interactive),
                message_count: int
            }
        """
        self.formatting_stats['messages_formatted'] += 1
        
        # Get scenario for button suggestions
        scenario = context.get('scenario', '')
        escalation = context.get('escalation')
        
        # Check if message needs splitting
        if len(agent_response) > self.MAX_LENGTH:
            # Split long message
            messages = self._split_long_message(agent_response)
            self.formatting_stats['messages_split'] += 1
            
            # Return first message with continuation indicator
            return {
                'text': messages,
                'type': 'text',
                'message_count': len(messages),
                'split': True
            }
        
        # Check if we should add buttons
        buttons = None
        message_type = 'text'
        
        if not escalation and scenario:
            # Add buttons for common actions
            buttons = self._suggest_buttons(scenario, context)
            if buttons:
                message_type = 'interactive'
                self.formatting_stats['buttons_added'] += 1
        
        return {
            'text': agent_response,
            'buttons': buttons,
            'type': message_type,
            'message_count': 1
        }
    
    def _split_long_message(self, text: str) -> List[str]:
        """
        Split messages longer than MAX_LENGTH
        
        Args:
            text: Long message text
        
        Returns:
            List of message chunks (each <= MAX_LENGTH)
        """
        if len(text) <= self.MAX_LENGTH:
            return [text]
        
        chunks = []
        
        # Try to split at sentence boundaries first
        sentences = re.split(r'([.!?]\s+)', text)
        
        if len(sentences) > 1:
            # Has sentence boundaries
            current_chunk = ""
            
            for i in range(0, len(sentences), 2):
                sentence = sentences[i]
                punctuation = sentences[i + 1] if i + 1 < len(sentences) else ''
                full_sentence = sentence + punctuation
                
                # Check if adding this sentence exceeds limit
                # (leave room for continuation indicator)
                if len(current_chunk) + len(full_sentence) + 20 > self.MAX_LENGTH:
                    if current_chunk:
                        # Save current chunk
                        chunks.append(current_chunk.strip())
                        current_chunk = full_sentence
                    else:
                        # Single sentence too long, force split by character
                        chunks.extend(self._split_by_chars(full_sentence))
                        current_chunk = ""
                else:
                    current_chunk += full_sentence
            
            # Add remaining chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
        else:
            # No sentence boundaries, split by character count
            chunks = self._split_by_chars(text)
        
        # Add continuation indicators
        for i in range(len(chunks) - 1):
            if len(chunks[i]) + 20 <= self.MAX_LENGTH:
                chunks[i] += "\n\n_(continued...)_"
        
        return chunks
    
    def _split_by_chars(self, text: str) -> List[str]:
        """
        Force split by character count (when no sentence boundaries)
        
        Args:
            text: Text to split
        
        Returns:
            List of chunks (each <= MAX_LENGTH)
        """
        chunks = []
        # Leave room for continuation indicator
        chunk_size = self.MAX_LENGTH - 20
        
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            chunks.append(chunk)
        
        return chunks
    
    def _suggest_buttons(self, scenario: str, context: Dict) -> Optional[List[Dict]]:
        """
        Add quick reply buttons based on scenario
        
        Args:
            scenario: Current conversation scenario
            context: Additional context
        
        Returns:
            List of button dicts or None
        """
        buttons = []
        
        # Order-related scenarios
        if 'order' in scenario.lower():
            order_data = context.get('order_data')
            
            if order_data:
                # Specific order buttons
                buttons.extend([
                    {
                        'type': 'reply',
                        'title': '📦 Track Order',
                        'id': 'track_order'
                    },
                    {
                        'type': 'reply',
                        'title': '🔄 Return Item',
                        'id': 'return_item'
                    }
                ])
            else:
                # General order help
                buttons.append({
                    'type': 'reply',
                    'title': '📦 My Orders',
                    'id': 'my_orders'
                })
        
        # Policy questions
        elif 'policy' in scenario.lower():
            buttons.extend([
                {
                    'type': 'reply',
                    'title': '↩️ Returns',
                    'id': 'return_policy'
                },
                {
                    'type': 'reply',
                    'title': '🚚 Shipping',
                    'id': 'shipping_policy'
                }
            ])
        
        # General queries
        elif scenario == 'general_query':
            buttons.extend([
                {
                    'type': 'reply',
                    'title': '📦 Track Order',
                    'id': 'track_order'
                },
                {
                    'type': 'reply',
                    'title': 'ℹ️ Help',
                    'id': 'help'
                }
            ])
        
        # Always add "Speak to Human" option
        if len(buttons) < self.MAX_BUTTONS:
            buttons.append({
                'type': 'reply',
                'title': '👤 Speak to Human',
                'id': 'speak_to_human'
            })
        
        # Limit to MAX_BUTTONS
        buttons = buttons[:self.MAX_BUTTONS]
        
        return buttons if buttons else None
    
    def format_for_whatsapp_api(
        self,
        formatted_response: Dict,
        recipient_phone: str
    ) -> Dict:
        """
        Format for actual WhatsApp Business API
        
        Args:
            formatted_response: Output from format_response()
            recipient_phone: Recipient's phone number
        
        Returns:
            WhatsApp API-compatible payload
        """
        # For text-only messages
        if formatted_response['type'] == 'text':
            # Check if split
            if formatted_response.get('split'):
                # Return multiple text messages
                return {
                    'messaging_product': 'whatsapp',
                    'recipient_type': 'individual',
                    'to': recipient_phone,
                    'type': 'text',
                    'text': {
                        'body': formatted_response['text'][0]  # Send first part
                    },
                    'note': f"Message split into {len(formatted_response['text'])} parts"
                }
            else:
                # Single text message
                return {
                    'messaging_product': 'whatsapp',
                    'recipient_type': 'individual',
                    'to': recipient_phone,
                    'type': 'text',
                    'text': {
                        'body': formatted_response['text']
                    }
                }
        
        # For interactive messages (with buttons)
        elif formatted_response['type'] == 'interactive':
            return {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': recipient_phone,
                'type': 'interactive',
                'interactive': {
                    'type': 'button',
                    'body': {
                        'text': formatted_response['text']
                    },
                    'action': {
                        'buttons': [
                            {
                                'type': 'reply',
                                'reply': {
                                    'id': btn['id'],
                                    'title': btn['title']
                                }
                            }
                            for btn in formatted_response['buttons']
                        ]
                    }
                }
            }
    
    def get_stats(self) -> Dict:
        """Get formatting statistics"""
        return {
            **self.formatting_stats,
            'split_rate': (
                self.formatting_stats['messages_split'] / 
                self.formatting_stats['messages_formatted'] * 100
            ) if self.formatting_stats['messages_formatted'] > 0 else 0
        }
    
    def __repr__(self) -> str:
        return f"WhatsAppResponseFormatter(formatted={self.formatting_stats['messages_formatted']})"


# Testing function
def test_whatsapp_formatter():
    """Test WhatsApp response formatter"""
    print("🧪 TESTING WHATSAPP RESPONSE FORMATTER")
    print("=" * 70)
    print()
    
    formatter = WhatsAppResponseFormatter()
    
    # Test 1: Short message
    print("TEST 1: Short Message (No Split)")
    short_response = "Your order #12345 is on its way! Expected delivery: Feb 5, 2026."
    
    result = formatter.format_response(short_response, {'scenario': 'order_status'})
    
    print(f"Text: {result['text'][:80]}...")
    print(f"Type: {result['type']}")
    print(f"Buttons: {len(result.get('buttons', []))} buttons")
    print(f"Message Count: {result['message_count']}")
    
    if result['buttons']:
        for btn in result['buttons']:
            print(f"  - {btn['title']}")
    
    assert result['message_count'] == 1, "Should be single message"
    assert len(result['text']) < 1600, "Should be under limit"
    print("✅ Short message formatted correctly")
    print()
    
    # Test 2: Long message (needs splitting)
    print("TEST 2: Long Message (Split Required)")
    long_response = "A" * 2000  # 2000 characters, no sentence boundaries
    
    result = formatter.format_response(long_response, {'scenario': 'general_query'})
    
    print(f"Message Count: {result['message_count']}")
    print(f"Split: {result.get('split')}")
    
    if result.get('split'):
        for i, chunk in enumerate(result['text'], 1):
            print(f"  Part {i}: {len(chunk)} chars")
            assert len(chunk) <= 1600, f"Chunk {i} ({len(chunk)} chars) exceeds 1600 limit!"
    
    assert result['message_count'] > 1, "Should be split"
    print("✅ Long message split correctly")
    print()
    
    # Test 3: Long message with sentences
    print("TEST 3: Long Message with Sentences")
    sentences = []
    for i in range(50):
        sentences.append(f"This is sentence number {i} in the long message. ")
    long_with_sentences = "".join(sentences)  # ~2000+ chars
    
    result = formatter.format_response(long_with_sentences, {'scenario': 'general_query'})
    
    print(f"Original Length: {len(long_with_sentences)} chars")
    print(f"Message Count: {result['message_count']}")
    
    for i, chunk in enumerate(result['text'], 1):
        print(f"  Part {i}: {len(chunk)} chars")
        assert len(chunk) <= 1600, f"Chunk {i} exceeds limit!"
    
    print("✅ Long message with sentences split correctly")
    print()
    
    # Test 4: Order status with buttons
    print("TEST 4: Order Status Response")
    order_response = "Your order is being shipped! Tracking: ABC123"
    
    result = formatter.format_response(
        order_response,
        {
            'scenario': 'order_status',
            'order_data': {'order_id': '12345', 'status': 'shipped'}
        }
    )
    
    print(f"Type: {result['type']}")
    print(f"Buttons: {[btn['title'] for btn in result.get('buttons', [])]}")
    
    assert result['type'] == 'interactive', "Should be interactive"
    assert result['buttons'] is not None, "Should have buttons"
    print("✅ Order status with buttons working")
    print()
    
    # Test 5: Policy question with buttons
    print("TEST 5: Policy Question Response")
    policy_response = "Our return policy allows returns within 30 days of purchase."
    
    result = formatter.format_response(
        policy_response,
        {'scenario': 'policy_question'}
    )
    
    print(f"Buttons: {[btn['title'] for btn in result.get('buttons', [])]}")
    
    has_return_btn = any('Return' in btn['title'] for btn in result.get('buttons', []))
    assert has_return_btn, "Should have return-related button"
    print("✅ Policy response with relevant buttons")
    print()
    
    # Test 6: WhatsApp API format
    print("TEST 6: WhatsApp API Format")
    simple_result = formatter.format_response(
        "Hello! How can I help?",
        {'scenario': 'general_query'}
    )
    
    api_payload = formatter.format_for_whatsapp_api(
        simple_result,
        recipient_phone="919876543210"
    )
    
    print(f"API Payload Keys: {list(api_payload.keys())}")
    print(f"Messaging Product: {api_payload.get('messaging_product')}")
    print(f"Type: {api_payload.get('type')}")
    
    assert api_payload['messaging_product'] == 'whatsapp', "Should be whatsapp"
    assert api_payload['to'] == "919876543210", "Should have recipient"
    print("✅ WhatsApp API format correct")
    print()
    
    # Test 7: Message with emojis
    print("TEST 7: Message with Emojis")
    emoji_response = "Hi there! 😊 Your order is on the way! 📦"
    
    result = formatter.format_response(emoji_response, {'scenario': 'order_status'})
    
    print(f"Text: {result['text']}")
    assert '😊' in result['text'], "Should preserve emojis"
    print("✅ Emojis preserved")
    print()
    
    # Summary
    print("=" * 70)
    stats = formatter.get_stats()
    print("FORMATTING STATISTICS:")
    print(f"  Messages Formatted: {stats['messages_formatted']}")
    print(f"  Messages Split: {stats['messages_split']}")
    print(f"  Buttons Added: {stats['buttons_added']}")
    print(f"  Split Rate: {stats['split_rate']:.1f}%")
    print()
    print("✅ WhatsApp Response Formatter tests complete!")


if __name__ == "__main__":
    test_whatsapp_formatter()
