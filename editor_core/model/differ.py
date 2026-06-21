"""
Differ for calculating model deltas.
Mirrors CKEditor 5 `model/differ.ts`.
"""

class Differ:
    """
    Buffers operations and calculates the delta to broadcast to clients/view.
    """
    def __init__(self):
        self._changes = []
        
    def buffer_operation(self, operation):
        self._changes.append(operation)
        
    def get_changes(self):
        # Simplified: just return buffered ops. 
        # In reality, this merges overlapping inserts/removes into a minimal delta.
        return self._changes
        
    def reset(self):
        self._changes = []
