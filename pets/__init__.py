"""Pet Agency - A virtual pet adoption system.

This module provides a minimal public API for the pet agency system.
Most internal implementation details are in submodules.
"""

# Main API
from .agency import Agency

# Constants needed by bin/ scripts
from .constants import (
    CORRAL,
    GENIE_EMOJI,
    PETS,
)

# Additional constants and utilities needed by tests
# (These could be removed if tests were refactored to not depend on them)
from .constants import (
    DAY_CARE_CENTER,
    HELP_TEXT,
    MYSTERY_HOME,
    NOISES,
    PET_BOREDOM_TIMES,
    SAD_MESSAGE_TEMPLATES,
    SPAWN_POINTS,
    THANKS_RESPONSES,
)
from .geometry import is_adjacent
from .lured import LURE_TIME_SECONDS

# Update queues module (needed by tests)
from . import update_queues

__all__ = [
    # Main API
    "Agency",
    # Constants for bin/ scripts
    "CORRAL",
    "GENIE_EMOJI",
    "PETS",
    # Test dependencies (could be removed with test refactoring)
    "DAY_CARE_CENTER",
    "HELP_TEXT",
    "MYSTERY_HOME",
    "NOISES",
    "PET_BOREDOM_TIMES",
    "SAD_MESSAGE_TEMPLATES",
    "SPAWN_POINTS",
    "THANKS_RESPONSES",
    "is_adjacent",
    "LURE_TIME_SECONDS",
    "update_queues",
]
