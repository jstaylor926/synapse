"""
RootElement for the model tree.
Mirrors CKEditor 5 `model/rootelement.ts`.
"""
from typing import Optional, Dict, Any
from .element import Element

class RootElement(Element):
    """The root element of a document."""
    def __init__(self, document, root_name: str = 'main'):
        super().__init__(root_name)
        self.document = document
        self.root_name = root_name
        
    @property
    def is_root(self) -> bool:
        return True
