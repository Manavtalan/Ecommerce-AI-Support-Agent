"""
Response Composer - Generates Focused, Context-Aware Responses
Uses intent analysis to create specific, helpful responses instead of info dumps
"""

from typing import Dict, Any, Optional, List
from core.intelligence.intent_classifier import UserIntent


class ResponseComposer:
    """
    Composes intelligent, focused responses based on user intent
    KEY PRINCIPLE: Answer ONLY what was asked, not everything you know
    """
    
    def __init__(self, brand_voice: Dict[str, str] = None):
        self.brand_voice = brand_voice or {}
        
    def compose(
        self,
        user_message: str,
        intent: UserIntent,
        tool_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Main composition method - creates the perfect response
        
        Args:
            user_message: What the user asked
            intent: Analyzed intent from IntentClassifier
            tool_results: Data from tools (order info, RAG, etc.)
            context: Conversation context
            
        Returns:
            Focused, helpful response string
        """
        
        # Handle missing data first
        if intent.missing_data:
            return self._compose_missing_data_response(intent)
        
        # Handle based on primary intent
        if intent.primary_intent == 'order_status_inquiry':
            return self._compose_order_status_response(
                intent, tool_results, user_message
            )
        
        elif intent.primary_intent == 'order_contents_inquiry':
            return self._compose_order_contents_response(intent, tool_results)
        
        elif intent.primary_intent == 'cancel_order':
            return self._compose_cancel_response(intent, tool_results)
        
        elif intent.primary_intent == 'refund_request':
            return self._compose_refund_response(intent, tool_results)
        
        elif intent.primary_intent == 'exchange_request':
            return self._compose_exchange_response(intent, tool_results)
        
        elif intent.primary_intent == 'change_address':
            return self._compose_change_address_response(intent, tool_results)
        
        elif intent.primary_intent == 'problem_report':
            return self._compose_problem_response(intent, tool_results)
        
        elif intent.primary_intent == 'policy_inquiry':
            return self._compose_policy_response(intent, tool_results)
        
        elif intent.primary_intent == 'product_inquiry':
            return self._compose_product_response(intent, tool_results)
        
        elif intent.primary_intent == 'greeting':
            return self._compose_greeting_response()
        
        elif intent.primary_intent == 'gratitude':
            return self._compose_gratitude_response()
        
        else:
            return self._compose_fallback_response()
    
    def _compose_missing_data_response(self, intent: UserIntent) -> str:
        """When we need more info from user"""
        
        if 'order_number' in intent.missing_data:
            return (
                "I'd be happy to help you with that! 😊\n\n"
                "Could you please share your order number? You can find it in your "
                "confirmation email - it usually looks like #12345."
            )
        
        if 'exchange_preference' in intent.missing_data:
            return (
                "I can help you with that exchange! 😊\n\n"
                "What size or color would you like to exchange it for?"
            )
        
        if 'reason' in intent.missing_data:
            return (
                "I'm here to help with your refund. Could you let me know "
                "the reason for the refund so I can assist you better?"
            )
        
        return "I'd be happy to help! Could you provide a bit more detail?"
    
    def _compose_order_status_response(
        self,
        intent: UserIntent,
        tool_results: Dict,
        user_message: str
    ) -> str:
        """
        Compose order status response - FOCUSED on specific question
        """
        order_data = tool_results.get('order_data', {})
        
        if not order_data:
            return self._compose_order_not_found_response()
        
        # Extract key info
        order_num = order_data.get('order_number', 'your order')
        product_name = order_data.get('product_name', 'your item')
        status = order_data.get('status', 'unknown')
        tracking = order_data.get('tracking_number')
        delivery_date = order_data.get('expected_delivery')
        current_location = order_data.get('last_known_location')
        
        # USER ASKED SPECIFIC QUESTION - ANSWER ONLY THAT
        
        if intent.specific_question == 'delivery_date':
            # They ONLY want delivery date
            if delivery_date:
                return (
                    f"Your order will arrive by **{delivery_date}**! 📦\n\n"
                    f"It's currently {status} and on its way to you. "
                    "Let me know if you need anything else!"
                )
            else:
                return (
                    f"Your order #{order_num} is currently **{status}**. "
                    "I don't have an exact delivery date yet, but I'll keep you updated!"
                )
        
        elif intent.specific_question == 'current_location':
            # They ONLY want location
            if current_location:
                return (
                    f"Your order #{order_num} is currently at **{current_location}** "
                    f"and is marked as **{status}**. 📍\n\n"
                    f"{('Expected delivery: ' + delivery_date) if delivery_date else ''}"
                )
            else:
                return (
                    f"Your order #{order_num} is **{status}**. "
                    "I don't have the exact location yet, but it's on its way!"
                )
        
        elif intent.specific_question == 'tracking_info':
            # They ONLY want tracking
            if tracking:
                return (
                    f"Your tracking number is: **{tracking}** 📦\n\n"
                    f"Status: {status}\n"
                    f"{('Expected delivery: ' + delivery_date) if delivery_date else ''}"
                )
            else:
                return (
                    f"Your order #{order_num} is **{status}**, but I don't see "
                    "a tracking number yet. It should be available soon!"
                )
        
        elif intent.specific_question == 'ship_date':
            # They want ship date
            ship_date = order_data.get('ship_date')
            if ship_date:
                return f"Your order was shipped on **{ship_date}**! 🚚"
            else:
                return (
                    f"Your order #{order_num} is currently **{status}**. "
                    "It hasn't shipped yet, but we're working on it!"
                )
        
        elif intent.specific_question == 'order_date':
            # They want order date
            order_date = order_data.get('order_date')
            if order_date:
                return f"You placed your order on **{order_date}**! 📅"
            else:
                return "Let me check when you placed this order..."
        
        else:
            # General order status query - give summary
            empathy = self._get_empathy_phrase(intent.user_emotion)
            
            return (
                f"{empathy}\n\n"
                f"Your order #{order_num} for **{product_name}** has been **{status}**! 🎉\n\n"
                f"{'📦 Tracking: ' + tracking if tracking else ''}\n"
                f"{'📅 Expected delivery: ' + delivery_date if delivery_date else ''}\n"
                f"{'📍 Current location: ' + current_location if current_location else ''}\n\n"
                "Let me know if you need anything else!"
            ).strip()
    
    def _compose_order_contents_response(self, intent: UserIntent, tool_results: Dict) -> str:
        """What's in the order - list items ONLY"""
        order_data = tool_results.get('order_data', {})
        
        product_name = order_data.get('product_name', 'Unknown item')
        variant = order_data.get('variant', '')
        quantity = order_data.get('quantity', 1)
        order_num = order_data.get('order_number')
        
        return (
            f"Your order #{order_num} contains:\n\n"
            f"• **{product_name}**"
            f"{' - ' + variant if variant else ''}"
            f" (Quantity: {quantity})\n\n"
            "Is there anything specific you'd like to know about this item?"
        )
    
    def _compose_cancel_response(self, intent: UserIntent, tool_results: Dict) -> str:
        """Cancel order - check status first, offer options"""
        order_data = tool_results.get('order_data', {})
        status = order_data.get('status', '').lower()
        order_num = order_data.get('order_number')
        
        empathy = self._get_empathy_phrase(intent.user_emotion)
        
        if status in ['pending', 'processing', 'confirmed']:
            # NOT SHIPPED - we can help cancel
            return (
                f"{empathy}\n\n"
                f"I can help you cancel order #{order_num}! Since it hasn't shipped yet, "
                "I can process the cancellation right away.\n\n"
                "Your refund will be processed within 5-7 business days.\n\n"
                "Would you like me to proceed with the cancellation?"
            )
        
        elif status in ['shipped', 'out for delivery']:
            # SHIPPED - can't cancel, but offer alternatives
            return (
                f"{empathy}\n\n"
                f"I see order #{order_num} has already been shipped, so we can't cancel it directly. "
                "But don't worry - here are your options:\n\n"
                "1. **Refuse delivery** - When it arrives, tell the delivery person you don't want it. "
                "It'll be sent back and you'll get a full refund.\n\n"
                "2. **Return after delivery** - Accept it and return within 30 days for a full refund.\n\n"
                "Which option works better for you?"
            )
        
        elif status == 'delivered':
            # DELIVERED - explain return process
            return (
                f"{empathy}\n\n"
                f"Order #{order_num} has been delivered, so we can't cancel it. "
                "However, you can return it within 30 days for a full refund!\n\n"
                "Would you like me to send you the return instructions?"
            )
        
        else:
            return "Let me check the status of your order and see what we can do..."
    
    def _compose_refund_response(self, intent: UserIntent, tool_results: Dict) -> str:
        """Similar to cancel - check status, offer options"""
        # Very similar logic to cancel_response
        return self._compose_cancel_response(intent, tool_results).replace(
            'cancel', 'process your refund for'
        )
    
    def _compose_exchange_response(self, intent: UserIntent, tool_results: Dict) -> str:
        """Exchange request - check status"""
        order_data = tool_results.get('order_data', {})
        status = order_data.get('status', '').lower()
        order_num = order_data.get('order_number')
        product_name = order_data.get('product_name')
        
        if status in ['pending', 'processing']:
            return (
                f"I can help you exchange your order! Since order #{order_num} hasn't "
                "shipped yet, I can update it for you.\n\n"
                "What size or color would you like instead?"
            )
        
        elif status in ['shipped', 'out for delivery']:
            return (
                f"I'd be happy to help with your exchange! Your order #{order_num} "
                f"for the {product_name} is currently on its way.\n\n"
                "Here's how our exchange process works:\n"
                "1. Receive your order first\n"
                "2. Initiate an exchange within 30 days\n"
                "3. We'll send you a return label\n"
                "4. Once we receive it back, we'll ship the new size/color\n\n"
                "What size or color would you like to exchange it for? "
                "I'll check if we have it in stock!"
            )
        
        else:
            return (
                "I'd be happy to help with your exchange! Our exchange policy allows "
                "you to exchange items within 30 days of delivery.\n\n"
                "What would you like to exchange it for?"
            )
    
    def _compose_change_address_response(self, intent: UserIntent, tool_results: Dict) -> str:
        """Change delivery address"""
        order_data = tool_results.get('order_data', {})
        status = order_data.get('status', '').lower()
        order_num = order_data.get('order_number')
        
        if status in ['pending', 'processing']:
            return (
                f"I can update the delivery address for order #{order_num}! "
                "Since it hasn't shipped yet, we can change it.\n\n"
                "What's the new address?"
            )
        
        else:
            return (
                f"Unfortunately, order #{order_num} has already shipped, so I can't "
                "change the delivery address anymore. 😔\n\n"
                "Your options are:\n"
                "1. Contact the courier directly to see if they can redirect it\n"
                "2. Have someone at the current address receive it and forward it to you\n\n"
                "Would either of these work?"
            )
    
    def _compose_problem_response(self, intent: UserIntent, tool_results: Dict) -> str:
        """Handle problem reports - HIGH EMPATHY"""
        problem_type = intent.problem_type
        order_data = tool_results.get('order_data', {})
        order_num = order_data.get('order_number', 'your order')
        
        if problem_type == 'damaged_item':
            return (
                "I'm so sorry to hear your item arrived damaged! 😔 "
                "That's absolutely not the quality we stand for.\n\n"
                "Let me make this right for you immediately. You have two options:\n\n"
                "1. **Full refund** - I can send you a return label and refund you as soon as we receive it back\n"
                "2. **Replacement** - I can send you a brand new one right away\n\n"
                "Which would you prefer? I want to resolve this as quickly as possible!"
            )
        
        elif problem_type == 'wrong_item':
            return (
                "Oh no - I'm really sorry you received the wrong item! 😔 "
                "That's completely our mistake.\n\n"
                f"Let me fix this for order #{order_num}:\n\n"
                "1. I'll send you the correct item immediately\n"
                "2. I'll send a return label for the wrong item - no rush to send it back\n\n"
                "Or if you prefer, I can process a full refund instead.\n\n"
                "Which would work better for you?"
            )
        
        elif problem_type == 'not_received':
            return (
                "I'm really sorry you haven't received your order yet! 😔 "
                "Let me help investigate this right away.\n\n"
                "First, could you check:\n"
                "1. With neighbors or building reception\n"
                "2. All entrances/porches\n"
                "3. If anyone else at your address received it\n\n"
                "If you still can't find it, I'll file a missing package claim immediately "
                "and either send a replacement or process a full refund.\n\n"
                "Have you checked those places?"
            )
        
        elif problem_type == 'delayed':
            return (
                "I completely understand how frustrating it is when an order is late! 😔\n\n"
                f"Let me check what's happening with order #{order_num}...\n\n"
                "[Include current status from order_data]\n\n"
                "I recommend:\n"
                "1. Keep tracking it for today\n"
                "2. If it doesn't arrive within 24 hours, contact the courier\n"
                "3. If still no luck, I can help you file a claim for replacement or refund\n\n"
                "I'm here to help - what would you like to do?"
            )
        
        else:
            return (
                "I'm sorry to hear you're having an issue! 😔\n\n"
                "I'm here to help resolve this. Could you tell me more about what happened?"
            )
    
    def _compose_policy_response(self, intent: UserIntent, tool_results: Dict) -> str:
        """Answer policy questions from RAG"""
        policy_info = tool_results.get('rag_results', [])
        
        if policy_info:
            # Use RAG results
            return (
                "Here's our policy:\n\n"
                f"{policy_info[0].get('content', 'Policy information...')}\n\n"
                "Does this answer your question?"
            )
        else:
            return (
                "I'd be happy to help with our policies! "
                "Could you be more specific about which policy you'd like to know about?"
            )
    
    def _compose_product_response(self, intent: UserIntent, tool_results: Dict) -> str:
        """Answer product questions"""
        product_info = tool_results.get('product_data', {})
        
        if product_info:
            return f"Here's what I can tell you about that product:\n\n{product_info}"
        else:
            return "Let me check on that product for you..."
    
    def _compose_greeting_response(self) -> str:
        """Friendly greeting"""
        return (
            "Hi there! 😊\n\n"
            "Welcome to FashionHub! How can I help you today?"
        )
    
    def _compose_gratitude_response(self) -> str:
        """Response to thanks"""
        return (
            "You're very welcome! 😊\n\n"
            "I'm always here if you need anything else. Happy shopping!"
        )
    
    def _compose_order_not_found_response(self) -> str:
        """When order doesn't exist"""
        return (
            "I couldn't find that order in our system. 😔\n\n"
            "This could mean:\n"
            "• The order number might be incorrect\n"
            "• There might be a typo\n\n"
            "Could you double-check your order number? You can find it in "
            "your confirmation email."
        )
    
    def _compose_fallback_response(self) -> str:
        """When we don't understand"""
        return (
            "I want to make sure I help you with exactly what you need! "
            "Could you tell me a bit more about what you're looking for? 😊"
        )
    
    def _get_empathy_phrase(self, emotion: str) -> str:
        """Get appropriate empathy phrase based on emotion"""
        
        if emotion == 'frustrated':
            return "I completely understand your frustration, and I'm here to help!"
        
        elif emotion == 'worried':
            return "I understand you're concerned - let me help put your mind at ease."
        
        elif emotion == 'urgent':
            return "I know this is urgent - let me help you right away!"
        
        elif emotion == 'happy':
            return "I'm so glad to hear that! 😊"
        
        elif emotion == 'confused':
            return "I'm happy to clarify that for you!"
        
        else:
            return "Hi! 😊"
