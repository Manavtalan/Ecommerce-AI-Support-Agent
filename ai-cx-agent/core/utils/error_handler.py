"""
Error Handler
Centralized error handling for all system failures
Handles: Tool failures, RAG failures, LLM failures, Invalid inputs, Conversation loops
"""

from typing import Dict, Optional
import time
from datetime import datetime


class ErrorHandler:
    """Centralized error handling system"""
    
    def __init__(self):
        """Initialize error handler"""
        self.error_log = []
        self.error_counts = {
            'tool_failures': 0,
            'rag_failures': 0,
            'llm_failures': 0,
            'invalid_inputs': 0,
            'conversation_loops': 0
        }
    
    def handle_tool_failure(
        self,
        tool_name: str,
        error: Exception,
        context: Dict
    ) -> Dict:
        """
        Handle tool execution failures
        
        Args:
            tool_name: Name of the failed tool
            error: Exception that occurred
            context: Additional context (user_message, params, etc.)
        
        Returns:
            {
                retry: bool,
                fallback_response: str,
                escalate: bool,
                log_data: dict
            }
        """
        self.error_counts['tool_failures'] += 1
        
        error_type = type(error).__name__
        error_message = str(error)
        
        # Determine if we should retry
        retry = self._should_retry_tool(error_type, tool_name)
        
        # Determine if we should escalate
        escalate = self._should_escalate_tool_error(error_type, context)
        
        # Build fallback response
        fallback_response = self._build_tool_fallback(tool_name, error_type, context)
        
        # Log error
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': 'tool_failure',
            'tool_name': tool_name,
            'exception_type': error_type,
            'exception_message': error_message,
            'context': context,
            'retry': retry,
            'escalate': escalate
        }
        
        self.error_log.append(log_data)
        
        print(f"⚠️  Tool Failure: {tool_name} - {error_type}")
        
        return {
            'retry': retry,
            'fallback_response': fallback_response,
            'escalate': escalate,
            'log_data': log_data
        }
    
    def handle_rag_failure(
        self,
        query: str,
        error: Exception
    ) -> Dict:
        """
        Handle RAG retrieval failures
        
        Args:
            query: Search query that failed
            error: Exception that occurred
        
        Returns:
            {
                retry: bool,
                fallback_response: str,
                use_llm_knowledge: bool,
                log_data: dict
            }
        """
        self.error_counts['rag_failures'] += 1
        
        error_type = type(error).__name__
        error_message = str(error)
        
        # Determine if we should retry
        retry = error_type in ['TimeoutError', 'ConnectionError']
        
        # Determine if we can use LLM's knowledge as fallback
        use_llm_knowledge = not retry
        
        # Build fallback response
        fallback_response = self._build_rag_fallback(query, error_type)
        
        # Log error
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': 'rag_failure',
            'query': query,
            'exception_type': error_type,
            'exception_message': error_message,
            'retry': retry,
            'use_llm_knowledge': use_llm_knowledge
        }
        
        self.error_log.append(log_data)
        
        print(f"⚠️  RAG Failure: {error_type} for query '{query[:50]}...'")
        
        return {
            'retry': retry,
            'fallback_response': fallback_response,
            'use_llm_knowledge': use_llm_knowledge,
            'log_data': log_data
        }
    
    def handle_llm_failure(
        self,
        prompt: str,
        error: Exception,
        retry_count: int = 0
    ) -> Dict:
        """
        Handle LLM API failures with exponential backoff
        
        Args:
            prompt: The prompt that failed
            error: Exception that occurred
            retry_count: Current retry attempt
        
        Returns:
            {
                retry: bool,
                wait_time: float (seconds),
                fallback_response: str,
                max_retries_reached: bool,
                log_data: dict
            }
        """
        self.error_counts['llm_failures'] += 1
        
        error_type = type(error).__name__
        error_message = str(error)
        
        # Check if error is retryable
        retryable_errors = [
            'RateLimitError',
            'APITimeoutError',
            'APIConnectionError',
            'InternalServerError'
        ]
        
        retry = error_type in retryable_errors and retry_count < 3
        
        # Calculate exponential backoff
        wait_time = self._calculate_backoff(retry_count) if retry else 0
        
        # Build fallback response
        fallback_response = self._build_llm_fallback(error_type)
        
        # Log error
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': 'llm_failure',
            'exception_type': error_type,
            'exception_message': error_message,
            'retry_count': retry_count,
            'retry': retry,
            'wait_time': wait_time,
            'prompt_length': len(prompt)
        }
        
        self.error_log.append(log_data)
        
        print(f"⚠️  LLM Failure: {error_type} (retry {retry_count}/3)")
        
        return {
            'retry': retry,
            'wait_time': wait_time,
            'fallback_response': fallback_response,
            'max_retries_reached': retry_count >= 3,
            'log_data': log_data
        }
    
    def handle_invalid_input(
        self,
        input_type: str,
        value: str,
        context: Dict
    ) -> Dict:
        """
        Handle invalid user inputs
        
        Args:
            input_type: Type of invalid input (empty, too_long, gibberish, etc.)
            value: The invalid value
            context: Additional context
        
        Returns:
            {
                response: str,
                request_clarification: bool,
                log_data: dict
            }
        """
        self.error_counts['invalid_inputs'] += 1
        
        # Build appropriate response
        response = self._build_invalid_input_response(input_type, value, context)
        
        # Determine if we need clarification
        request_clarification = input_type in ['empty', 'ambiguous', 'gibberish']
        
        # Log error
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': 'invalid_input',
            'input_type': input_type,
            'value_length': len(value),
            'context': context
        }
        
        self.error_log.append(log_data)
        
        print(f"⚠️  Invalid Input: {input_type}")
        
        return {
            'response': response,
            'request_clarification': request_clarification,
            'log_data': log_data
        }
    
    def handle_conversation_loop(
        self,
        loop_count: int,
        context: Dict
    ) -> Dict:
        """
        Handle repeated questions (conversation loops)
        
        Args:
            loop_count: Number of times question repeated
            context: Conversation context
        
        Returns:
            {
                escalate: bool,
                try_different_approach: bool,
                response: str,
                log_data: dict
            }
        """
        self.error_counts['conversation_loops'] += 1
        
        # Escalate if loop is severe (3+ repetitions)
        escalate = loop_count >= 3
        
        # Try different approach if not escalating
        try_different_approach = loop_count == 2 and not escalate
        
        # Build response
        response = self._build_loop_response(loop_count, context)
        
        # Log error
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': 'conversation_loop',
            'loop_count': loop_count,
            'context': context,
            'escalate': escalate
        }
        
        self.error_log.append(log_data)
        
        print(f"⚠️  Conversation Loop Detected: {loop_count} repetitions")
        
        return {
            'escalate': escalate,
            'try_different_approach': try_different_approach,
            'response': response,
            'log_data': log_data
        }
    
    # === HELPER METHODS ===
    
    def _should_retry_tool(self, error_type: str, tool_name: str) -> bool:
        """Determine if tool failure should be retried"""
        retryable_errors = ['TimeoutError', 'ConnectionError', 'HTTPError']
        return error_type in retryable_errors
    
    def _should_escalate_tool_error(self, error_type: str, context: Dict) -> bool:
        """Determine if tool error should escalate to human"""
        # Escalate if critical tool (order_status) fails
        critical_tools = ['get_order_status']
        is_critical = context.get('tool_name') in critical_tools
        
        # Escalate if error is permanent (not timeout)
        is_permanent = error_type not in ['TimeoutError', 'ConnectionError']
        
        return is_critical and is_permanent
    
    def _calculate_backoff(self, retry_count: int) -> float:
        """Calculate exponential backoff time"""
        base = 1.0  # 1 second
        return base * (2 ** retry_count)  # 1s, 2s, 4s, 8s...
    
    def _build_tool_fallback(
        self,
        tool_name: str,
        error_type: str,
        context: Dict
    ) -> str:
        """Build fallback response for tool failure"""
        
        if error_type in ['TimeoutError', 'ConnectionError']:
            return "I'm having trouble accessing that information right now. Let me try again, or I can connect you with our support team."
        
        if tool_name == 'get_order_status':
            return "I'm unable to retrieve your order details at the moment. Please provide your email address, and I'll look it up another way, or I can connect you with our support team."
        
        if tool_name == 'search_knowledge':
            return "I want to give you accurate information. Let me connect you with our support team who can help you with this."
        
        return "I'm experiencing a technical issue. Let me connect you with our support team who can assist you better."
    
    def _build_rag_fallback(self, query: str, error_type: str) -> str:
        """Build fallback response for RAG failure"""
        
        if error_type in ['TimeoutError', 'ConnectionError']:
            return "I'm having trouble accessing our knowledge base. Let me try to help based on what I know."
        
        return "I want to ensure I give you accurate information. Let me connect you with our support team."
    
    def _build_llm_fallback(self, error_type: str) -> str:
        """Build fallback response for LLM failure"""
        
        if error_type == 'RateLimitError':
            return "I'm experiencing high traffic right now. Please bear with me for a moment."
        
        if error_type in ['APITimeoutError', 'APIConnectionError']:
            return "I'm having a connection issue. Let me try that again."
        
        return "I'm here to help! Could you please rephrase your question?"
    
    def _build_invalid_input_response(
        self,
        input_type: str,
        value: str,
        context: Dict
    ) -> str:
        """Build response for invalid input"""
        
        if input_type == 'empty':
            return "I didn't receive your message. Could you please send it again?"
        
        if input_type == 'too_long':
            return "That's a lot of information! Could you break it down into smaller questions so I can help you better?"
        
        if input_type == 'gibberish':
            return "I'm having trouble understanding. Could you rephrase that for me?"
        
        if input_type == 'ambiguous':
            return "I want to make sure I understand correctly. Could you provide a bit more detail?"
        
        if input_type == 'invalid_order':
            return "I couldn't find that order number. Could you verify the order number or provide the email address used for the order?"
        
        return "I'm here to help! Could you provide more details about what you need?"
    
    def _build_loop_response(self, loop_count: int, context: Dict) -> str:
        """Build response for conversation loop"""
        
        if loop_count == 2:
            return "I understand this is important to you. Let me try explaining differently: " + context.get('alternative_explanation', 'Let me connect you with our support team.')
        
        if loop_count >= 3:
            return "I want to make sure you get the help you need. Let me connect you with our support team who can assist you better."
        
        return "Let me help you with that."
    
    def get_error_summary(self) -> Dict:
        """Get summary of all errors"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'by_type': self.error_counts.copy(),
            'recent_errors': self.error_log[-10:] if self.error_log else []
        }
    
    def clear_errors(self):
        """Clear error log and counts"""
        self.error_log = []
        self.error_counts = {k: 0 for k in self.error_counts}
    
    def __repr__(self) -> str:
        total = sum(self.error_counts.values())
        return f"ErrorHandler(total_errors={total})"


# Create __init__.py for utils module
def create_init():
    """Create __init__.py for utils module"""
    import os
    init_path = os.path.join(os.path.dirname(__file__), '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write('"""Utility modules"""\n')


if __name__ == "__main__":
    # Test error handler
    print("🧪 TESTING ERROR HANDLER")
    print("=" * 70)
    print()
    
    handler = ErrorHandler()
    
    # Test 1: Tool failure
    print("TEST 1: Tool Failure")
    result = handler.handle_tool_failure(
        'get_order_status',
        TimeoutError("Connection timeout"),
        {'user_message': 'Where is my order?', 'tool_name': 'get_order_status'}
    )
    print(f"  Retry: {result['retry']}")
    print(f"  Escalate: {result['escalate']}")
    print(f"  Fallback: {result['fallback_response'][:60]}...")
    print()
    
    # Test 2: LLM failure
    print("TEST 2: LLM Failure")
    result = handler.handle_llm_failure(
        "What is your return policy?",
        Exception("RateLimitError"),
        retry_count=1
    )
    print(f"  Retry: {result['retry']}")
    print(f"  Wait: {result['wait_time']}s")
    print(f"  Fallback: {result['fallback_response'][:60]}...")
    print()
    
    # Test 3: Invalid input
    print("TEST 3: Invalid Input")
    result = handler.handle_invalid_input(
        'gibberish',
        'asdfghjkl',
        {}
    )
    print(f"  Response: {result['response']}")
    print(f"  Request clarification: {result['request_clarification']}")
    print()
    
    # Test 4: Conversation loop
    print("TEST 4: Conversation Loop")
    result = handler.handle_conversation_loop(
        3,
        {'last_question': 'Where is my order?'}
    )
    print(f"  Escalate: {result['escalate']}")
    print(f"  Response: {result['response'][:60]}...")
    print()
    
    # Summary
    summary = handler.get_error_summary()
    print("=" * 70)
    print("ERROR SUMMARY")
    print(f"Total Errors: {summary['total_errors']}")
    print(f"By Type: {summary['by_type']}")
    print()
    
    print("✅ Error handler tests complete!")
    
    # Create __init__.py
    create_init()
