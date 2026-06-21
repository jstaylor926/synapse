"""
History of operations.
Mirrors CKEditor 5 `model/history.ts`.
"""
from typing import List

class History:
    """Holds a log of operations applied to the document."""
    def __init__(self):
        self._operations = []
        
    def add_operation(self, operation):
        self._operations.append(operation)
        
    def get_operations(self, base_version: int = 0) -> List:
        """Gets all operations from a specific base version."""
        # In CKEditor, operations carry their base_version, so we filter by it
        return [op for op in self._operations if getattr(op, 'base_version', -1) >= base_version]
