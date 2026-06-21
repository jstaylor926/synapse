"""
Insert Operation.
Mirrors CKEditor 5 `model/operation/insertoperation.ts`.
"""
from typing import List
from .operation import Operation
from ..tree.position import Position
from ..tree.node import Node

class InsertOperation(Operation):
    """Inserts nodes at a given position."""
    def __init__(self, position: Position, nodes: List[Node], base_version: int):
        super().__init__(base_version)
        self.position = position
        self.nodes = nodes
        
    @property
    def type(self) -> str:
        return 'insert'
        
    def execute(self):
        """Executes the insert on the model tree."""
        parent = self.position.parent
        offset = self.position.offset
        parent._insert_children(offset, self.nodes)
        
    def get_reversed(self) -> Operation:
        from .move_operation import MoveOperation
        from ..tree.range import Range
        # A remove is represented as moving to the graveyard
        # For simplicity in this scaffold, we'll just mock it
        length = sum(n.offset_size for n in self.nodes)
        source_range = Range(self.position, self.position.get_shifted_by(length))
        graveyard_pos = Position(self.position.root.document.get_root('graveyard'), [0])
        return MoveOperation(source_range, graveyard_pos, self.base_version + 1)
