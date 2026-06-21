"""
Selection in the model tree.
Mirrors CKEditor 5 `model/selection.ts`.
"""
from typing import List, Optional, Any, Dict
from .range import Range
from ...utils.observable import ObservableMixin

class Selection(ObservableMixin):
    """Represents a document selection."""
    def __init__(self, ranges: Optional[List[Range]] = None):
        super().__init__()
        self._ranges = ranges or []
        self._attributes = {}
        
    @property
    def ranges(self) -> List[Range]:
        return self._ranges
        
    @property
    def is_collapsed(self) -> bool:
        return len(self._ranges) == 1 and self._ranges[0].is_collapsed

    def get_attribute(self, key: str) -> Any:
        return self._attributes.get(key)
        
    def set_attribute(self, key: str, value: Any):
        self._attributes[key] = value
        self.fire('change:attribute', key, value)
