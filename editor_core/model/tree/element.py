"""
Element node for the model tree.
Mirrors CKEditor 5 `model/element.ts`.
"""
from typing import List, Optional, Dict, Any
from .node import Node

class Element(Node):
    """An element in the model tree."""
    def __init__(self, name: str, attributes: Optional[Dict[str, Any]] = None, children: Optional[List[Node]] = None):
        super().__init__(attributes)
        self.name = name
        self._children: List[Node] = []
        
        if children:
            self._insert_children(0, children)

    @property
    def is_element(self) -> bool:
        return True
        
    def get_child(self, index: int) -> Optional[Node]:
        if 0 <= index < len(self._children):
            return self._children[index]
        return None
        
    def get_child_index(self, node: Node) -> Optional[int]:
        try:
            return self._children.index(node)
        except ValueError:
            return None
            
    def _insert_children(self, index: int, nodes: List[Node]):
        """Internal method to insert children and update their parents."""
        for i, node in enumerate(nodes):
            node.parent = self
            self._children.insert(index + i, node)
            
    def _remove_children(self, index: int, count: int) -> List[Node]:
        """Internal method to remove children."""
        removed = self._children[index:index+count]
        for node in removed:
            node.parent = None
        del self._children[index:index+count]
        return removed

    @property
    def child_count(self) -> int:
        return len(self._children)
        
    @property
    def max_offset(self) -> int:
        """The total offset size of all children."""
        return sum(child.offset_size for child in self._children)
