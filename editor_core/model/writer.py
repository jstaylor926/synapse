"""
Writer API for mutating the model tree.
Mirrors CKEditor 5 `model/writer.ts`.
"""
from typing import Any
from .tree.position import Position
from .tree.element import Element
from .tree.text import Text
from .batch import Batch

class Writer:
    """
    API to mutate the model tree.
    All changes must go through the writer so they are recorded as Operations.
    """
    def __init__(self, model, batch: Batch):
        self.model = model
        self.batch = batch
        
    def insert(self, item: Any, position: Position):
        """Inserts an item at the given position."""
        # Generates an InsertOperation
        from .operation.insert_operation import InsertOperation
        
        # Determine size of item
        if isinstance(item, str):
            item = Text(item)
            
        nodes = [item] if not isinstance(item, list) else item
        
        op = InsertOperation(position, nodes, self.model.document.version)
        self.model.apply_operation(op)
        
    def insert_text(self, text: str, position: Position):
        """Convenience method for text."""
        self.insert(Text(text), position)
        
    def remove(self, range_to_remove):
        """Removes a range."""
        pass # Generates RemoveOperation (often represented as MoveOperation to graveyard)
        
    def move(self, source_range, target_position: Position):
        """Moves a range to a target position."""
        from .operation.move_operation import MoveOperation
        op = MoveOperation(source_range, target_position, self.model.document.version)
        self.model.apply_operation(op)
