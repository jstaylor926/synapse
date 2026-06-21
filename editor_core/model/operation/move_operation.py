"""
Move Operation.
Mirrors CKEditor 5 `model/operation/moveoperation.ts`.
"""
from .operation import Operation
from ..tree.position import Position
from ..tree.range import Range

class MoveOperation(Operation):
    """Moves a range of nodes to a new position."""
    def __init__(self, source_range: Range, target_position: Position, base_version: int):
        super().__init__(base_version)
        self.source_range = source_range
        self.target_position = target_position
        
    @property
    def type(self) -> str:
        return 'move'
        
    def execute(self):
        """Executes the move on the model tree."""
        source_parent = self.source_range.start.parent
        source_offset = self.source_range.start.offset
        count = self.source_range.get_difference()
        
        # Remove
        removed_nodes = source_parent._remove_children(source_offset, count)
        
        # Insert
        target_parent = self.target_position.parent
        target_offset = self.target_position.offset
        target_parent._insert_children(target_offset, removed_nodes)
        
    def get_reversed(self) -> Operation:
        # Move back
        count = self.source_range.get_difference()
        new_source_range = Range(self.target_position, self.target_position.get_shifted_by(count))
        return MoveOperation(new_source_range, self.source_range.start, self.base_version + 1)
