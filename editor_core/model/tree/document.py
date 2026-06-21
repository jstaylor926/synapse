"""
Document class.
Mirrors CKEditor 5 `model/document.ts`.
"""
from typing import Dict
from .rootelement import RootElement
from .selection import Selection
from ...utils.observable import ObservableMixin
from ..history import History

class Document(ObservableMixin):
    """
    The document model.
    Holds the root elements, history, and version.
    """
    def __init__(self):
        super().__init__()
        self.roots: Dict[str, RootElement] = {}
        self.selection = Selection()
        self.history = History()
        self.version = 0
        
        self.create_root('main')
        
    def create_root(self, name: str = 'main') -> RootElement:
        """Creates a new root element."""
        root = RootElement(self, name)
        self.roots[name] = root
        return root
        
    def get_root(self, name: str = 'main') -> RootElement:
        return self.roots.get(name)
