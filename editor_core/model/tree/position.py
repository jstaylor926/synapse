"""
Position in the model tree.
Mirrors CKEditor 5 `model/position.ts`.
"""
from typing import List, Optional
from .node import Node
from .element import Element

class Position:
    """Represents a position in the model tree."""
    def __init__(self, root: Element, path: List[int]):
        self.root = root
        self.path = list(path)
        
    @property
    def parent(self) -> Element:
        """Gets the parent element at this position."""
        node = self.root
        for index in self.path[:-1]:
            if node.is_element:
                node = node.get_child(index)
        return node
        
    @property
    def offset(self) -> int:
        """Gets the offset within the parent."""
        if not self.path:
            return 0
        return self.path[-1]

    def get_shifted_by(self, shift: int) -> 'Position':
        """Returns a new position shifted by the given offset."""
        new_path = list(self.path)
        new_path[-1] += shift
        return Position(self.root, new_path)
