"""
Model Controller.
Mirrors CKEditor 5 `model/model.ts`.
"""
from typing import Callable, Any
from .tree.document import Document
from .schema import Schema
from .differ import Differ
from .writer import Writer
from .batch import Batch
from ..utils.observable import ObservableMixin

class Model(ObservableMixin):
    """
    The main controller for the Model subsystem.
    Manages the document, schema, and operation application.
    """
    def __init__(self):
        super().__init__()
        self.document = Document()
        self.schema = Schema()
        self.differ = Differ()
        
        # Listeners for OT mechanics: buffer in differ, apply to history
        self.on('applyOperation', self._buffer_in_differ, priority='high')
        self.on('applyOperation', self._update_history, priority='low')
        
    def change(self, callback: Callable[[Writer], Any]) -> Any:
        """
        Executes a callback with a Writer to mutate the document.
        All mutations are grouped in a single Batch.
        """
        batch = Batch()
        writer = Writer(self, batch)
        result = callback(writer)
        
        # After change block, the model fires events (in reality, using enqueueChange)
        self.fire('change:data', batch)
        return result

    def apply_operation(self, operation):
        """
        Applies an operation to the model.
        This method is dynamically decorated by `ObservableMixin.decorate` so
        listeners can intercept it before/after execution.
        """
        # In actual CKEditor, this is decorated: self.decorate('apply_operation')
        # Here we mimic the decorated execution:
        self.fire('applyOperation', operation)
        operation.execute()

    def _buffer_in_differ(self, event_info, operation):
        """High priority listener: buffers the operation before execution."""
        self.differ.buffer_operation(operation)

    def _update_history(self, event_info, operation):
        """Low priority listener: logs the operation and bumps version after execution."""
        self.document.history.add_operation(operation)
        self.document.version += 1

# Manually decorate apply_operation
Model().decorate('apply_operation')
