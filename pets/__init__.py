"""Pet Agency - A virtual pet adoption system."""

# Public API exports for backward compatibility

# Core classes
from .agency import Agency, reset_agency
from .pet import Pet

# Geometry utilities
from .geometry import (
    parse_position,
    position_tuple,
    offset_position,
    is_adjacent,
    Region,
    DELTAS,
)

# Configuration and constants
from .constants import (
    # Pet and manner constants
    MANNERS,
    PETS,
    ANIMAL_NAMES,
    MANNER_WORDS,
    MANNER_PREFIXES,
    # Genie configuration
    GENIE_NAME,
    GENIE_EMOJI,
    GENIE_HOME,
    SPAWN_POINTS,
    MYSTERY_HOME,
    # Game regions
    CORRAL,
    DAY_CARE_CENTER,
    # Game constants
    PET_BOREDOM_TIMES,
    # Message templates
    HELP_TEXT,
    NOISES,
    SAD_MESSAGE_TEMPLATES,
    THANKS_RESPONSES,
)

# Lure constants
from .lured import LURE_TIME_SECONDS

# Parser (commonly used in tests)
from .parser import parse_command

# Update queues (used in tests)
from . import update_queues

__all__ = [
    # Core classes
    "Agency",
    "reset_agency",
    "Pet",
    # Geometry utilities
    "parse_position",
    "position_tuple",
    "offset_position",
    "is_adjacent",
    "Region",
    "DELTAS",
    # Configuration and constants
    "MANNERS",
    "PETS",
    "ANIMAL_NAMES",
    "MANNER_WORDS",
    "MANNER_PREFIXES",
    "GENIE_NAME",
    "GENIE_EMOJI",
    "GENIE_HOME",
    "SPAWN_POINTS",
    "MYSTERY_HOME",
    "CORRAL",
    "DAY_CARE_CENTER",
    "PET_BOREDOM_TIMES",
    "HELP_TEXT",
    "NOISES",
    "SAD_MESSAGE_TEMPLATES",
    "THANKS_RESPONSES",
    "LURE_TIME_SECONDS",
    # Parser
    "parse_command",
    # Update queues module
    "update_queues",
]
