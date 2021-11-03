"""Print stuff unless it shouldn't"""
from . import config

def log(*msg, **kwargs):
    """Print msg unless quiet"""
    if not config.quiet:
        print(*msg, **kwargs)

def debug(*msg, **kwargs):
    """Print msg if verbose"""
    if config.verbose:
        print(*msg, **kwargs)

def critical(*msg, **kwargs):
    """Print msg"""
    print(*msg, **kwargs)
