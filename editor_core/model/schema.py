"""
Document Schema.
Mirrors CKEditor 5 `model/schema.ts`.
"""

class Schema:
    """
    Defines what is allowed in the model.
    """
    def __init__(self):
        self._items = {}
        
    def register(self, item_name: str, definition: dict):
        self._items[item_name] = definition
        
    def check_child(self, context: str, child_name: str) -> bool:
        """Checks if child_name is allowed inside context."""
        context_def = self._items.get(context, {})
        allowed_children = context_def.get('allowIn', [])
        return child_name in allowed_children or '$text' in allowed_children
