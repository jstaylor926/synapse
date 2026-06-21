"""
Range in the model tree.
Mirrors CKEditor 5 `model/range.ts`.
"""
from .position import Position

class Range:
    """Represents a range in the model tree."""
    def __init__(self, start: Position, end: Position = None):
        self.start = start
        self.end = end if end else start

    @property
    def is_collapsed(self) -> bool:
        """True if the range is collapsed (start and end are the same)."""
        return self.start.path == self.end.path and self.start.root == self.end.root
        
    def get_difference(self) -> int:
        """Difference in offset between start and end (assuming same parent)."""
        if self.start.path[:-1] == self.end.path[:-1]:
            return self.end.path[-1] - self.start.path[-1]
        return 0 # Simplified
