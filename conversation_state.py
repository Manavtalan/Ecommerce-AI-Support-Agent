# conversation_state.py
"""
Semantic Conversation State - Single Source of Truth
This replaces fragmented last_* flags with explicit topic tracking.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class TopicType(Enum):
    """What kind of thing we're discussing"""
    NONE = "none"
    ORDER = "order"
    POLICY = "policy"
    GENERAL = "general"


class TopicConfidence(Enum):
    """How certain are we about this topic?"""
    EXPLICIT = "explicit"    # User clearly stated
    INFERRED = "inferred"    # Carried from context
    NONE = "none"            # No topic


@dataclass(frozen=True)
class ActiveTopic:
    """
    Immutable representation of conversational focus.
    This is THE answer to: "What are we currently discussing?"
    """
    
    topic_type: TopicType
    entity_id: Optional[str]      # e.g., order_id "12345"
    confidence: TopicConfidence
    reason: str                   # Human-readable explanation
    established_at: datetime
    
    def __post_init__(self):
        """Enforce invariants at construction"""
        if self.topic_type == TopicType.NONE:
            if self.entity_id is not None:
                raise ValueError("NONE topic cannot have entity_id")
            if self.confidence != TopicConfidence.NONE:
                raise ValueError("NONE topic must have NONE confidence")
        
        if self.topic_type != TopicType.NONE:
            if self.confidence == TopicConfidence.NONE:
                raise ValueError("Non-NONE topic must have confidence")
    
    def is_active(self) -> bool:
        """Is there an active topic?"""
        return self.topic_type != TopicType.NONE
    
    def is_order_topic(self) -> bool:
        """Are we discussing a specific order?"""
        return self.topic_type == TopicType.ORDER and self.entity_id is not None
    
    def is_explicit(self) -> bool:
        """Was this explicitly stated by user?"""
        return self.confidence == TopicConfidence.EXPLICIT
    
    def __str__(self) -> str:
        if not self.is_active():
            return "ActiveTopic(NONE)"
        return (
            f"ActiveTopic({self.topic_type.value}:{self.entity_id}, "
            f"{self.confidence.value}, reason='{self.reason}')"
        )


# Sentinel: "no active topic"
NO_TOPIC = ActiveTopic(
    topic_type=TopicType.NONE,
    entity_id=None,
    confidence=TopicConfidence.NONE,
    reason="No active topic",
    established_at=datetime.now()
)