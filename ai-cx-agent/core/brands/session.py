"""
Brand Session Manager
Manages brand-scoped sessions with data isolation
"""

import uuid
from typing import Dict, Optional, Any
from datetime import datetime
from core.brands.registry import get_brand_registry


class BrandSession:
    """Brand-scoped session with complete data isolation"""
    
    def __init__(self, brand_id: str, session_id: Optional[str] = None):
        """
        Initialize brand session
        
        Args:
            brand_id: Brand identifier
            session_id: Optional session ID (auto-generated if not provided)
        """
        # Validate brand exists
        registry = get_brand_registry()
        if not registry.validate_brand_id(brand_id):
            raise ValueError(f"Invalid brand_id: {brand_id}")
        
        self.brand_id = brand_id
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        
        # Load brand configuration
        self.brand_config = registry.get_brand_by_id(brand_id)
        
        # Session metadata
        self.metadata = {
            "messages_count": 0,
            "tools_used": [],
            "rag_queries": 0
        }
    
    def get_brand_config(self) -> Dict:
        """
        Get full brand configuration
        
        Returns:
            Brand config dict
        """
        return self.brand_config
    
    def get_brand_scope(self) -> Dict[str, Any]:
        """
        Get brand scope for database queries
        
        Returns:
            Dict with brand_id for filtering
        """
        return {"brand_id": self.brand_id}
    
    def validate_access(self, resource: Dict) -> bool:
        """
        Validate if current session can access a resource
        
        Args:
            resource: Resource dict with brand_id
        
        Returns:
            True if access allowed
        
        Raises:
            PermissionError if access denied
        """
        resource_brand = resource.get("brand_id")
        
        if resource_brand != self.brand_id:
            raise PermissionError(
                f"Cross-brand access denied: Session brand '{self.brand_id}' "
                f"cannot access resource from brand '{resource_brand}'"
            )
        
        return True
    
    def get_voice_config(self) -> Dict:
        """Get brand voice configuration"""
        return self.brand_config.get("voice", {})
    
    def get_policies(self) -> Dict:
        """Get brand policies"""
        return self.brand_config.get("policies", {})
    
    def get_integrations(self) -> Dict:
        """Get brand integrations"""
        return self.brand_config.get("integrations", {})
    
    def update_activity(self):
        """Update last active timestamp"""
        self.last_active = datetime.now()
        self.metadata["messages_count"] += 1
    
    def log_tool_use(self, tool_name: str):
        """Log tool usage"""
        if tool_name not in self.metadata["tools_used"]:
            self.metadata["tools_used"].append(tool_name)
    
    def log_rag_query(self):
        """Log RAG query"""
        self.metadata["rag_queries"] += 1
    
    def get_session_summary(self) -> Dict:
        """Get session summary"""
        return {
            "session_id": self.session_id,
            "brand_id": self.brand_id,
            "brand_name": self.brand_config.get("name"),
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata
        }
    
    def __repr__(self) -> str:
        return f"BrandSession(brand={self.brand_id}, session={self.session_id[:8]}...)"


# Session factory
def create_brand_session(brand_id: str) -> BrandSession:
    """
    Create a new brand session
    
    Args:
        brand_id: Brand identifier
    
    Returns:
        New BrandSession instance
    """
    return BrandSession(brand_id)
