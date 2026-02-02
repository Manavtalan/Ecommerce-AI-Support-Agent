"""Integration modules for various platforms"""

from .whatsapp_adapter import WhatsAppMessageAdapter
from .whatsapp_formatter import WhatsAppResponseFormatter
from .email_adapter import EmailAdapter
from .instagram_adapter import InstagramDMAdapter

__all__ = [
    'WhatsAppMessageAdapter',
    'WhatsAppResponseFormatter',
    'EmailAdapter',
    'InstagramDMAdapter'
]
