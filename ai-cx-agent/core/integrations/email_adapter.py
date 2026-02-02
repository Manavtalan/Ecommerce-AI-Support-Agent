"""
Email Adapter
Handles email conversations with thread continuity
Features: HTML formatting, email signatures, thread management
"""

from typing import Dict, Optional
import re
from datetime import datetime


class EmailAdapter:
    """Handles email conversations"""
    
    def __init__(self, brand_config: Optional[Dict] = None):
        """
        Initialize email adapter
        
        Args:
            brand_config: Brand configuration with email signature
        """
        self.brand_config = brand_config or {}
        self.thread_cache = {}
    
    def parse_email(self, email_data: Dict) -> Dict:
        """
        Parse incoming email
        
        Args:
            email_data: {
                subject: str,
                body: str,
                thread_id: str (optional),
                from: str,
                to: str,
                html_body: str (optional)
            }
        
        Returns:
            {
                user_message: str,
                session_id: str (thread_id),
                user_email: str,
                context: dict
            }
        """
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        html_body = email_data.get('html_body', '')
        thread_id = email_data.get('thread_id', self._generate_thread_id(email_data.get('from')))
        from_email = email_data.get('from', '')
        
        # Clean email body (remove signatures, quoted text)
        cleaned_body = self._clean_email_body(body)
        
        # Extract user message
        user_message = cleaned_body if cleaned_body else subject
        
        # Store thread context
        self._update_thread_context(thread_id, {
            'from': from_email,
            'subject': subject,
            'last_message': user_message
        })
        
        return {
            'user_message': user_message,
            'session_id': thread_id,
            'user_email': from_email,
            'context': {
                'platform': 'email',
                'subject': subject,
                'thread_id': thread_id
            }
        }
    
    def format_email_response(
        self,
        response: str,
        context: Dict
    ) -> Dict:
        """
        Format agent response as HTML email
        
        Args:
            response: Agent's text response
            context: {
                subject: str,
                thread_id: str,
                user_email: str,
                brand_config: dict (optional)
            }
        
        Returns:
            {
                subject: str,
                body_text: str,
                body_html: str,
                thread_id: str,
                in_reply_to: str (optional)
            }
        """
        subject = context.get('subject', 'Re: Your inquiry')
        thread_id = context.get('thread_id')
        
        # Add "Re:" if not already present
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}"
        
        # Build HTML email
        body_html = self._build_html_email(response, context)
        
        # Plain text version
        body_text = self._html_to_text(response)
        
        return {
            'subject': subject,
            'body_text': body_text,
            'body_html': body_html,
            'thread_id': thread_id,
            'in_reply_to': thread_id  # For email threading
        }
    
    def _clean_email_body(self, body: str) -> str:
        """
        Clean email body (remove signatures, quoted text)
        
        Args:
            body: Raw email body
        
        Returns:
            Cleaned message
        """
        # Remove common signature markers
        signature_patterns = [
            r'\n--\s*\n.*',  # -- signature
            r'\nSent from my.*',  # Sent from my iPhone/Android
            r'\nGet Outlook for.*',  # Get Outlook
            r'\n_{3,}.*',  # _____ signature
        ]
        
        cleaned = body
        for pattern in signature_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove quoted text (starts with >)
        lines = cleaned.split('\n')
        filtered_lines = [line for line in lines if not line.strip().startswith('>')]
        cleaned = '\n'.join(filtered_lines)
        
        # Remove "On [date], [person] wrote:" patterns
        cleaned = re.sub(
            r'\n\s*On .+ wrote:\s*\n.*',
            '',
            cleaned,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        return cleaned.strip()
    
    def _build_html_email(self, response: str, context: Dict) -> str:
        """
        Build HTML email with brand styling
        
        Args:
            response: Agent response text
            context: Context with brand config
        
        Returns:
            HTML email string
        """
        brand_config = context.get('brand_config', self.brand_config)
        brand_name = brand_config.get('name', 'Our Team')
        brand_color = brand_config.get('color', '#4F46E5')
        
        # Convert plain text to HTML paragraphs
        paragraphs = response.split('\n\n')
        html_content = ''.join(f'<p>{p.replace(chr(10), "<br>")}</p>' for p in paragraphs if p.strip())
        
        # Email signature
        signature = self._build_signature(brand_config)
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            border-bottom: 3px solid {brand_color};
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .content {{
            margin: 20px 0;
        }}
        .content p {{
            margin: 15px 0;
        }}
        .signature {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 14px;
        }}
        .signature strong {{
            color: {brand_color};
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin: 0; color: {brand_color};">{brand_name} Support</h2>
    </div>
    
    <div class="content">
        {html_content}
    </div>
    
    <div class="signature">
        {signature}
    </div>
</body>
</html>
"""
        return html_template.strip()
    
    def _build_signature(self, brand_config: Dict) -> str:
        """Build email signature"""
        brand_name = brand_config.get('name', 'Our Team')
        support_email = brand_config.get('support_email', 'support@example.com')
        website = brand_config.get('website', 'www.example.com')
        
        return f"""
        <strong>Best regards,</strong><br>
        {brand_name} Customer Support<br>
        <br>
        📧 {support_email}<br>
        🌐 {website}
        """
    
    def _html_to_text(self, html_or_text: str) -> str:
        """Convert HTML to plain text (simple version)"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_or_text)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        return text.strip()
    
    def _generate_thread_id(self, email: str) -> str:
        """Generate thread ID from email"""
        import hashlib
        hash_obj = hashlib.sha256(f"{email}{datetime.now().date()}".encode())
        return f"email_{hash_obj.hexdigest()[:16]}"
    
    def _update_thread_context(self, thread_id: str, context: Dict):
        """Update thread context"""
        if thread_id not in self.thread_cache:
            self.thread_cache[thread_id] = {
                'created_at': datetime.now().isoformat(),
                'message_count': 0
            }
        
        self.thread_cache[thread_id].update(context)
        self.thread_cache[thread_id]['message_count'] += 1
        self.thread_cache[thread_id]['updated_at'] = datetime.now().isoformat()
    
    def get_thread_context(self, thread_id: str) -> Optional[Dict]:
        """Get thread context"""
        return self.thread_cache.get(thread_id)
    
    def __repr__(self) -> str:
        return f"EmailAdapter(active_threads={len(self.thread_cache)})"


# Testing function
def test_email_adapter():
    """Test email adapter"""
    print("🧪 TESTING EMAIL ADAPTER")
    print("=" * 70)
    print()
    
    adapter = EmailAdapter(brand_config={
        'name': 'FashionHub',
        'color': '#FF6B6B',
        'support_email': 'support@fashionhub.com',
        'website': 'www.fashionhub.com'
    })
    
    # Test 1: Parse email
    print("TEST 1: Parse Incoming Email")
    email_data = {
        'subject': 'Question about my order',
        'body': '''Hi,

I wanted to ask about my order #12345. When will it arrive?

Thanks,
John

--
Sent from my iPhone''',
        'from': 'john@example.com',
        'to': 'support@fashionhub.com'
    }
    
    parsed = adapter.parse_email(email_data)
    print(f"User Message: {parsed['user_message']}")
    print(f"Session ID: {parsed['session_id']}")
    print(f"User Email: {parsed['user_email']}")
    print(f"✅ Email parsed and cleaned")
    print()
    
    # Test 2: Format response
    print("TEST 2: Format Email Response")
    response = "Your order #12345 is currently being shipped and will arrive by February 5th. You can track it here: track.example.com/12345"
    
    formatted = adapter.format_email_response(response, {
        'subject': email_data['subject'],
        'thread_id': parsed['session_id'],
        'user_email': parsed['user_email'],
        'brand_config': adapter.brand_config
    })
    
    print(f"Subject: {formatted['subject']}")
    print(f"Thread ID: {formatted['thread_id']}")
    print(f"Body Text: {formatted['body_text'][:80]}...")
    print(f"Has HTML: {len(formatted['body_html']) > 0}")
    print(f"✅ Response formatted")
    print()
    
    # Test 3: HTML email
    print("TEST 3: HTML Email Content")
    print(formatted['body_html'][:300] + "...")
    print(f"✅ HTML email generated")
    print()
    
    # Test 4: Thread continuity
    print("TEST 4: Thread Continuity")
    thread_context = adapter.get_thread_context(parsed['session_id'])
    print(f"Thread messages: {thread_context['message_count']}")
    print(f"From: {thread_context['from']}")
    print(f"✅ Thread context maintained")
    print()
    
    print("=" * 70)
    print(f"Active Threads: {len(adapter.thread_cache)}")
    print()
    print("✅ Email Adapter tests complete!")


if __name__ == "__main__":
    test_email_adapter()
