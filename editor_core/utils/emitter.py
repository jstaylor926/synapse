"""
Event info and EmitterMixin.
Mirrors CKEditor 5 `emittermixin.ts` and `eventinfo.ts`.
"""
from typing import Any, Callable, Dict, List, Tuple
from .priorities import get_priority

class EventInfo:
    def __init__(self, source: Any, name: str):
        self.source = source
        self.name = name
        self.path = [source]
        self._stop_called = False
        self.return_value = None

    def stop(self):
        """Stops event propagation."""
        self._stop_called = True

    @property
    def stop_called(self) -> bool:
        return self._stop_called


class EmitterMixin:
    """
    Mixin that provides event firing and listening capabilities.
    """
    def __init__(self):
        # Dictionary of event_name -> list of (priority, callback)
        self._listeners: Dict[str, List[Tuple[float, Callable]]] = {}

    def on(self, event_name: str, callback: Callable, priority: str | float = 'normal'):
        """Registers an event listener."""
        if not hasattr(self, '_listeners'):
            self._listeners = {}
            
        if event_name not in self._listeners:
            self._listeners[event_name] = []
            
        p = get_priority(priority)
        self._listeners[event_name].append((p, callback))
        # Sort listeners by priority descending
        self._listeners[event_name].sort(key=lambda x: x[0], reverse=True)

    def off(self, event_name: str, callback: Callable):
        """Unregisters an event listener."""
        if hasattr(self, '_listeners') and event_name in self._listeners:
            self._listeners[event_name] = [
                (p, cb) for p, cb in self._listeners[event_name] if cb != callback
            ]

    def fire(self, event_name: str, *args, **kwargs) -> Any:
        """Fires an event, calling all registered listeners."""
        if not hasattr(self, '_listeners'):
            return None
            
        event_info = EventInfo(self, event_name)
        
        # We allow firing generic events like `change` which also triggers `change:property`
        # But for exact matches:
        if event_name in self._listeners:
            for _, callback in self._listeners[event_name]:
                callback(event_info, *args, **kwargs)
                if event_info.stop_called:
                    break
                    
        return event_info.return_value
