"""
Base Tool Class
Foundation for all agent tools
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Tool(ABC):
    """Base class for all tools"""
    
    def __init__(self, name: str, description: str):
        """
        Initialize tool
        
        Args:
            name: Tool name
            description: What the tool does
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool
        
        Args:
            **kwargs: Tool-specific parameters
        
        Returns:
            Result dict with 'success', 'data', 'error'
        """
        pass
    
    def validate_params(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate tool parameters
        
        Args:
            **kwargs: Parameters to validate
        
        Returns:
            (is_valid, error_message)
        """
        return True, None
    
    def format_result(self, success: bool, data: Any = None, error: str = None) -> Dict:
        """
        Format tool result
        
        Args:
            success: Whether execution succeeded
            data: Result data
            error: Error message if failed
        
        Returns:
            Formatted result dict
        """
        return {
            "success": success,
            "data": data,
            "error": error,
            "tool": self.name
        }
    
    def __repr__(self) -> str:
        return f"Tool(name={self.name})"


class ToolExecutionError(Exception):
    """Raised when tool execution fails"""
    pass
