"""
Utility functions for logging.
"""

def indent(string: str, space_count: int = 4):
    return (' ' * space_count) + string.replace('\n', '\n' + (' ' * space_count))
