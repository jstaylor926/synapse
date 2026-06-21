"""
Observable functionality and method decoration.
Mirrors CKEditor 5 `observablemixin.ts`.
"""
from typing import Any, Callable
from .emitter import EmitterMixin

class ObservableMixin(EmitterMixin):
    """
    Provides property observation and method decoration (event interception).
    """
    def __init__(self):
        super().__init__()
        self._observable_properties = {}

    def set(self, name: str, value: Any):
        """Sets an observable property and fires change events."""
        old_value = self._observable_properties.get(name)
        if old_value != value:
            self._observable_properties[name] = value
            self.fire(f'change:{name}', name, value, old_value)
            self.fire('change', name, value, old_value)

    def get(self, name: str) -> Any:
        return self._observable_properties.get(name)

    def decorate(self, method_name: str):
        """
        Decorates a method so its execution fires pre/post events.
        This is a cornerstone of CKEditor's architecture: methods like
        `applyOperation` are decorated so extensions can intercept them
        with priority listeners.
        """
        original_method = getattr(self, method_name)
        
        # If already decorated, do nothing
        if getattr(original_method, '_is_decorated', False):
            return

        def decorated_method(*args, **kwargs):
            # Fire the high-priority interceptors
            event_args = (args, kwargs)
            
            # The pattern: `fire('methodName', args...)`
            # Listeners can modify args, return early, or stop propagation
            event_info = type('MockEventInfo', (), {'name': method_name, 'return_value': None, 'stop_called': False, 'source': self})()
            
            # Fire event to allow interception
            if hasattr(self, '_listeners') and method_name in self._listeners:
                for _, callback in self._listeners[method_name]:
                    callback(event_info, *event_args[0], **event_args[1])
                    if event_info.stop_called:
                        return event_info.return_value

            # Call original method
            result = original_method(*args, **kwargs)
            return result

        decorated_method._is_decorated = True
        # Re-bind the decorated method to the instance
        setattr(self, method_name, decorated_method)
