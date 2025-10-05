"""Pet Agency - A virtual pet adoption system.

This module provides the public API for the pet agency system.
"""

# Main API
from .agency import Agency

# Constants needed by bin/ scripts
from .constants import (
    CORRAL,
    GENIE_EMOJI,
    PETS,
)

__all__ = [
    "Agency",
    "CORRAL",
    "GENIE_EMOJI",
    "PETS",
]
