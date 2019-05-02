"""
This module is supposed to contain quite a few nice-to-have
exceptions, but is quite pitiful at the moment (TODO).
"""

class UnresponsiveMEAMEError(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors
