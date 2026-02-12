"""
Base Tool Class - Required by knowledge_tool, product_tool, shipping_tool
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Tool(ABC):
    """Base class for all tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass
    
    def validate_params(self, **kwargs) -> tuple:
        return True, None
    
    def format_result(self, success: bool, data: Any = None, error: str = None) -> Dict:
        return {
            "success": success,
            "data": data,
            "error": error,
            "tool": self.name
        }
    
    def __repr__(self) -> str:
        return f"Tool(name={self.name})"


class ToolExecutionError(Exception):
    pass
