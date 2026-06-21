"""
Batch of operations.
Mirrors CKEditor 5 `model/batch.ts`.
"""
from typing import List

class Batch:
    """A logical grouping of operations (e.g., a single undo step)."""
    def __init__(self, type_name: str = 'transparent'):
        self.type = type_name
        self.operations = []
        
    def add_operation(self, operation):
        self.operations.append(operation)
