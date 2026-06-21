"""
Split Operation.
Mirrors CKEditor 5 `model/operation/splitoperation.ts`.
"""
from .operation import Operation
from ..tree.position import Position

class SplitOperation(Operation):
    """Splits an element into two."""
    def __init__(self, split_position: Position, how_many: int, insertion_position: Position, base_version: int):
        super().__init__(base_version)
        self.split_position = split_position
        self.how_many = how_many
        self.insertion_position = insertion_position
        
    @property
    def type(self) -> str:
        return 'split'
        
    def execute(self):
        pass # Structural split logic here
        
    def get_reversed(self) -> Operation:
        # Reverse is MergeOperation
        pass
