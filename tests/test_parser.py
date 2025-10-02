import pytest
from pets.parser import parse_command


@pytest.mark.parametrize(
    "phrase,expected_animal",
    [
        ("adopt a sheep please", "sheep"),
        ("adopt the sheep", "sheep"),
        ("adopt a dog", "dog"),
        ("adopt a pet dog", "dog"),
        ("adopt the pet cat please", "cat"),
        ("May I please adopt a pet sheep", "sheep"),
        ("adopt the unicorn", "unicorn"),
        ("adopt one rabbit", "rabbit"),
        ("adopt a pet please", "pet"),
        ("adopt a pet s'il vous plait", "pet"),
        ("adopt an animal", "animal"),
        ("adopt the genie please", "genie"),
        ("adopt the kittens please", "kittens"),
    ],
)
def test_adoption_phrase_parsing(phrase, expected_animal):
    """Test that various adoption phrases correctly parse the animal type."""
    result = parse_command(phrase)
    assert result is not None, f"Failed to parse: {phrase}"
    command, args = result
    animal_type = args[1]
    assert command == "adoption", f"Wrong command for: {phrase}"
    assert (
        animal_type == expected_animal
    ), f"Expected {expected_animal}, got {animal_type} for: {phrase}"
