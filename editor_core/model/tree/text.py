"""
Text node for the model tree.
Mirrors CKEditor 5 `model/text.ts`.
"""
from typing import Optional, Dict, Any
from .node import Node

class Text(Node):
    """A text node in the model tree."""
    def __init__(self, data: str, attributes: Optional[Dict[str, Any]] = None):
        super().__init__(attributes)
        self.data = data
        
    @property
    def is_text(self) -> bool:
        return True
        
    @property
    def offset_size(self) -> int:
        """Text node offset size is the string length."""
        return len(self.data)
