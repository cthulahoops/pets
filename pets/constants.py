"""Game configuration and constants for the pets module."""

import os
import textwrap
from .geometry import parse_position, position_tuple, offset_position, Region


MANNERS = [
    "please",
    "bitte",
    "le do thoil",
    "sudo",
    "per favore",
    "oh mighty djinn",
    "s'il vous plaît",
    "s'il vous plait",
    "svp",
    "por favor",
    "kudasai",
    "onegai shimasu",
    "пожалуйста",
]

PETS = [
    {"emoji": "🦇", "name": "bat", "noise": "screech!"},
    {"emoji": "🐻", "name": "bear", "noise": "ROAR!"},
    {"emoji": "🐝", "name": "bee", "noise": "buzz!"},
    {"emoji": "🦕", "name": "brontosaurus", "noise": "MEEEHHH!"},
    {"emoji": "🐫", "name": "camel"},
    {"emoji": "🐈", "name": "cat", "noise": "miaow!"},
    {"emoji": "🐛", "name": "caterpillar", "noise": "munch!"},
    {"emoji": "🐄", "name": "cow", "noise": "Moo!"},
    {"emoji": "🦀", "name": "crab", "noise": "click!"},
    {"emoji": "🐊", "name": "crocodile"},
    {"emoji": "🐕", "name": "dog", "noise": "woof!"},
    {"emoji": "🐉", "name": "dragon", "noise": "🔥"},
    {"emoji": "🦅", "name": "eagle"},
    {"emoji": "🐘", "name": "elephant"},
    {"emoji": "🦩", "name": "flamingo"},
    {"emoji": "🦊", "name": "fox", "noise": "Wrahh!"},
    {"emoji": "🐸", "name": "frog", "noise": "ribbet!"},
    {"emoji": "🦒", "name": "giraffe"},
    {"emoji": "🦔", "name": "hedgehog", "noise": "scurry, scurry, scurry"},
    {"emoji": "🦛", "name": "hippo"},
    {"emoji": "👾", "name": "invader"},
    {"emoji": "🦘", "name": "kangaroo", "noise": "Chortle chortle!"},
    {"emoji": "🐨", "name": "koala", "noise": "gggrrrooowwwlll"},
    {"emoji": "🦙", "name": "llama"},
    {"emoji": "🐁", "name": "mouse", "noise": "squeak!"},
    {"emoji": "🦉", "name": "owl", "noise": "hoot hoot!"},
    {"emoji": "🦜", "name": "parrot", "noise": "HELLO!"},
    {"emoji": "🐧", "name": "penguin"},
    {"emoji": "🐖", "name": "pig", "noise": "oink!"},
    {"emoji": "🐇", "name": "rabbit"},
    {"emoji": "🚀", "name": "rocket"},
    {"emoji": "🐌", "name": "snail", "noise": "slurp!"},
    {"emoji": "🦖", "name": "t-rex", "noise": "RAWR!"},
    {"emoji": "🐅", "name": "tiger"},
    {"emoji": "🐢", "name": "turtle", "noise": "hiss!"},
    {"emoji": "🦄", "name": "unicorn", "noise": "✨"},
    {"emoji": "🪨", "name": "rock", "noise": "🤘"},
    {"emoji": "🦥", "name": "sloth", "noise": "zzzzzzzzzzzz..."},
    {"emoji": "🐙", "name": "octopus", "noise": "Never Graduate!"},
    {"emoji": "🐇", "name": "rabbit"},
    {"emoji": "🦭", "name": "seal", "noise": "bork bork!"},
    {"emoji": "🤖", "name": "robot", "noise": "beep boop"},
]

# Derived constants
ANIMAL_NAMES = {pet["name"].lower() for pet in PETS}
MANNER_WORDS = {manner.lower() for manner in MANNERS}

# Precompute manner prefixes for efficient matching
# Split multi-word manners and get their first words for prefix matching
MANNER_PREFIXES = set()
for manner in MANNER_WORDS:
    first_word = manner.split()[0]
    MANNER_PREFIXES.add(first_word)


GENIE_NAME = os.environ.get("GENIE_NAME", "Pet Agency Genie")
GENIE_EMOJI = "🧞"
GENIE_HOME = parse_position(os.environ.get("GENIE_HOME", "60,15"))

SPAWN_POINTS = {
    position_tuple(offset_position(GENIE_HOME, {"x": dx, "y": dy}))
    for (dx, dy) in [
        (-2, -2),
        (0, -2),
        (2, -2),
        (-2, 0),
        (2, 0),
        (0, 2),
        (2, 2),
        (-4, 1),
        (-5, 1),
        (-6, 1),
        (-7, 1),
        (-7, 2),
    ]
}

MYSTERY_HOME = offset_position(GENIE_HOME, {"x": 5, "y": 2})

CORRAL = Region({"x": 0, "y": 40}, {"x": 19, "y": 58})
DAY_CARE_CENTER = Region({"x": 0, "y": 62}, {"x": 11, "y": 74})


PET_BOREDOM_TIMES = (3600, 5400)


HELP_TEXT = textwrap.dedent(
    """\
    I can help you adopt a pet! Just send me a message saying 'adopt the <pet type> please'.
    The agency is just north of the main space. Drop by to see the available pets, and read more instructions on the note by the door."""
)

NOISES = {pet["emoji"]: pet.get("noise", "💖") for pet in PETS}

SAD_MESSAGE_TEMPLATES = [
    "Was I not a good {pet_name}?",
    "I thought you liked me.",
    "😢",
    "What will I do now?",
    "But where will I go?",
    "One day I might learn to trust again...",
    "I only wanted to make you happy.",
    "My heart hurts.",
    "Did I do something wrong?",
    "But why?",
    "💔",
]

THANKS_RESPONSES = ["You're welcome!", "No problem!", "❤️"]
