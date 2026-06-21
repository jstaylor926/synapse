"""
Base Operation.
Mirrors CKEditor 5 `model/operation/operation.ts`.
"""

class Operation:
    """
    Base class for all OT operations.
    """
    def __init__(self, base_version: int):
        self.base_version = base_version
        self.is_document_operation = True
        
    def execute(self):
        """Applies the operation to the tree."""
        raise NotImplementedError
        
    def get_reversed(self) -> 'Operation':
        """Returns the inverse of this operation."""
        raise NotImplementedError
        
    def to_json(self) -> dict:
        """Serializes the operation for network transmission."""
        return {'baseVersion': self.base_version}
