"""
Structured Logger
Production-grade JSON logging for observability
Integrates with: PostHog, Sentry, DataDog, Grafana
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Optional, Any


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage(),
        }
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class StructuredLogger:
    """Production-grade structured logging"""
    
    def __init__(self, service_name: str = "ai-cx-agent"):
        """
        Initialize structured logger
        
        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # JSON formatter for structured logs
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def log_event(
        self,
        event: str,
        level: str = "INFO",
        brand_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ):
        """
        Log structured event
        
        Args:
            event: Event name (e.g., "order_lookup", "escalation")
            level: Log level (INFO, WARNING, ERROR)
            brand_id: Brand identifier
            session_id: Conversation session ID
            **kwargs: Additional fields
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "level": level,
            "event": event,
            "brand_id": brand_id,
            "session_id": session_id,
            **kwargs
        }
        
        # Create log record with extra fields
        extra = {'extra_fields': log_data}
        
        if level == "ERROR":
            self.logger.error(event, extra=extra)
        elif level == "WARNING":
            self.logger.warning(event, extra=extra)
        else:
            self.logger.info(event, extra=extra)
    
    def log_conversation_turn(
        self,
        brand_id: str,
        session_id: str,
        user_message: str,
        agent_response: str,
        metadata: Dict
    ):
        """
        Log complete conversation turn
        
        Args:
            brand_id: Brand identifier
            session_id: Session ID
            user_message: User's message
            agent_response: Agent's response
            metadata: Conversation metadata
        """
        self.log_event(
            event="conversation_turn",
            brand_id=brand_id,
            session_id=session_id,
            user_message_length=len(user_message),
            agent_response_length=len(agent_response),
            emotion=metadata.get('emotion'),
            emotion_intensity=metadata.get('intensity'),
            quality_score=metadata.get('quality_score', {}).get('overall'),
            quality_grade=metadata.get('quality_score', {}).get('grade'),
            tool_used=metadata.get('tool_used'),
            tool_success=metadata.get('tool_success'),
            escalation=bool(metadata.get('escalation')),
            escalation_tier=metadata.get('escalation', {}).get('escalation_tier') if metadata.get('escalation') else None,
            context_maintained=metadata.get('context_maintained', False)
        )
    
    def log_tool_call(
        self,
        brand_id: str,
        tool_name: str,
        success: bool,
        latency_ms: int,
        session_id: Optional[str] = None,
        **kwargs
    ):
        """
        Log tool execution
        
        Args:
            brand_id: Brand identifier
            tool_name: Name of tool
            success: Whether tool succeeded
            latency_ms: Execution time in milliseconds
            session_id: Session ID (optional)
            **kwargs: Additional fields
        """
        self.log_event(
            event="tool_call",
            brand_id=brand_id,
            session_id=session_id,
            tool=tool_name,
            success=success,
            latency_ms=latency_ms,
            **kwargs
        )
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        brand_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ):
        """
        Log error
        
        Args:
            error_type: Type of error
            error_message: Error message
            brand_id: Brand identifier (optional)
            session_id: Session ID (optional)
            **kwargs: Additional fields
        """
        self.log_event(
            event="error",
            level="ERROR",
            brand_id=brand_id,
            session_id=session_id,
            error_type=error_type,
            error_message=error_message,
            **kwargs
        )
    
    def log_llm_call(
        self,
        brand_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        success: bool,
        session_id: Optional[str] = None
    ):
        """
        Log LLM API call
        
        Args:
            brand_id: Brand identifier
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            latency_ms: API latency
            success: Whether call succeeded
            session_id: Session ID (optional)
        """
        self.log_event(
            event="llm_call",
            brand_id=brand_id,
            session_id=session_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            success=success
        )
    
    def log_escalation(
        self,
        brand_id: str,
        session_id: str,
        escalation_tier: int,
        reason: str,
        prevented: bool = False
    ):
        """
        Log escalation event
        
        Args:
            brand_id: Brand identifier
            session_id: Session ID
            escalation_tier: Tier (1-3)
            reason: Escalation reason
            prevented: Whether escalation was prevented
        """
        self.log_event(
            event="escalation" if not prevented else "escalation_prevented",
            level="WARNING" if not prevented else "INFO",
            brand_id=brand_id,
            session_id=session_id,
            escalation_tier=escalation_tier,
            reason=reason,
            prevented=prevented
        )
    
    def log_integration_event(
        self,
        platform: str,
        event_type: str,
        success: bool,
        brand_id: Optional[str] = None,
        **kwargs
    ):
        """
        Log integration event (WhatsApp, Email, etc.)
        
        Args:
            platform: Platform name (whatsapp, email, instagram)
            event_type: Event type (message_received, message_sent)
            success: Whether event succeeded
            brand_id: Brand identifier (optional)
            **kwargs: Additional fields
        """
        self.log_event(
            event=f"integration_{event_type}",
            brand_id=brand_id,
            platform=platform,
            success=success,
            **kwargs
        )
    
    def __repr__(self) -> str:
        return f"StructuredLogger(service={self.service_name})"


# Global logger instance
logger = StructuredLogger()
