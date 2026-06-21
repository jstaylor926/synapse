"""
Base Node for the model tree.
Mirrors CKEditor 5 `model/node.ts`.
"""
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .element import Element
    from .rootelement import RootElement

class Node:
    """Base class for model tree nodes."""
    def __init__(self, attributes: Optional[Dict[str, Any]] = None):
        self._attributes = dict(attributes) if attributes else {}
        self.parent: Optional['Element'] = None
        self.start_offset: Optional[int] = None
        
    @property
    def is_node(self) -> bool:
        return True
        
    @property
    def is_element(self) -> bool:
        return False
        
    @property
    def is_text(self) -> bool:
        return False

    @property
    def is_root(self) -> bool:
        return False

    def get_attribute(self, key: str) -> Any:
        return self._attributes.get(key)
        
    def has_attribute(self, key: str) -> bool:
        return key in self._attributes
        
    def get_attributes(self) -> Dict[str, Any]:
        return self._attributes.copy()
        
    @property
    def root(self) -> 'Node':
        """Returns the root node of the tree this node is attached to."""
        node = self
        while node.parent is not None:
            node = node.parent
        return node
        
    @property
    def index(self) -> Optional[int]:
        """Returns the index of this node in its parent's children array."""
        if not self.parent:
            return None
        return self.parent.get_child_index(self)
        
    @property
    def offset_size(self) -> int:
        """The size of this node. Texts return length, elements return 1."""
        return 1
