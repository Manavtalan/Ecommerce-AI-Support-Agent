# error_handler.py
"""
Professional Error Handling
Clean messages for customers, detailed logs for debugging.
"""

import logging
from typing import Callable


class ErrorHandler:
    """Graceful error handling with customer-friendly messages"""
    
    ERROR_MESSAGES = {
        "api_timeout": "I'm experiencing a brief delay. Let me connect you with our team.",
        "order_not_found": "I couldn't locate that order. Could you double-check the order number?",
        "invalid_format": "That doesn't look like a valid order number. Order numbers are typically 4-6 digits.",
        "system_error": "I'm having technical difficulties. Let me forward you to our support team.",
        "llm_error": "I'm having trouble processing that. Let me connect you with support."
    }
    
    @staticmethod
    def handle_error(error_type: str, exception: Exception = None) -> str:
        """
        Get customer-friendly error message and log technical details.
        """
        if exception:
            logging.error(f"{error_type}: {str(exception)}")
        
        return ErrorHandler.ERROR_MESSAGES.get(
            error_type,
            ErrorHandler.ERROR_MESSAGES["system_error"]
        )
    
    @staticmethod
    def safe_execute(func: Callable, error_type: str = "system_error"):
        """
        Decorator for safe function execution.
        
        Usage:
            @ErrorHandler.safe_execute
            def risky_function():
                ...
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in {func.__name__}: {e}")
                return ErrorHandler.handle_error(error_type, e)
        
        return wrapper