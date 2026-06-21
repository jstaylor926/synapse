"""
String to numeric priority mapping.
Mirrors CKEditor 5 `priorities.ts`.
"""

PRIORITIES = {
    'highest': 100000,
    'high': 1000,
    'normal': 0,
    'low': -1000,
    'lowest': -100000
}

def get_priority(priority: str | int | float) -> float:
    """Returns the numeric priority."""
    if isinstance(priority, str):
        return PRIORITIES.get(priority, 0)
    return float(priority)
