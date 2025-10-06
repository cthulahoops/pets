from collections import namedtuple
import asyncio
import itertools
from datetime import datetime

import pytest

from pets import Agency
from pets.constants import (
    PETS,
    SPAWN_POINTS,
    THANKS_RESPONSES,
    NOISES,
    DAY_CARE_CENTER,
    SAD_MESSAGE_TEMPLATES,
    MYSTERY_HOME,
    HELP_TEXT,
)
from pets.geometry import is_adjacent
import pets.update_queues
import pets.constants
import pets.lured

# Reduce the sleep delay in the bot update code so tests run faster.
pets.update_queues.SLEEP_AFTER_UPDATE = 0.01
pets.constants.PET_BOREDOM_TIMES = (1, 1)

Request = namedtuple("Request", ("method", "path", "id", "json"))


class MockSession:
    def __init__(self, get_data):
        self._queue = asyncio.Queue()
        self.get_data = get_data
        self.ids = itertools.count(9999)

    async def get(self, path):
        return self.get_data[path]

    async def post(self, path, json):
        print("POST: ", path, json)
        if path == "bots":
            bot_json = json["bot"]
            return {
                "name": bot_json["name"],
                "id": next(self.ids),
                "emoji": bot_json["emoji"],
                "pos": {"x": bot_json["x"], "y": bot_json["y"]},
                "direction": bot_json["direction"],
            }
        await self._queue.put(Request("post", path, None, json))

    async def patch(self, path, bot_id, json):
        await self._queue.put(Request("patch", path, bot_id, json))

    async def delete(self, path, bot_id):
        await self._queue.put(Request("delete", path, bot_id, None))

    async def get_request(self):
        return await asyncio.wait_for(self._queue.get(), 0.1)

    def pending_requests(self):
        return not self._queue.empty()

    async def message_received(self, sender, recipient):
        request = await self.get_request()
        message = request.json
        assert message["bot_id"] == sender["id"]
        message_text = message["text"]
        mention = f"@**{recipient['person_name']}** "
        assert message_text[: len(mention)] == mention
        return message_text[len(mention) :]

    async def moved_to(self):
        request = await self.get_request()
        return request.json["bot"]


@pytest.fixture(name="genie")
def genie_fixture():
    return {
        "type": "Bot",
        "id": 1,
        "emoji": "🧞",
        "name": "Unit Genie",
        "pos": {"x": -7, "y": -9},
    }


@pytest.fixture(name="rocket")
def rocket_fixture():
    return {
        "type": "Bot",
        "id": 39887,
        "name": "rocket",
        "emoji": "🚀",
        "pos": {"x": 1, "y": 1},
    }


@pytest.fixture(name="person")
def person_fixture():
    return {
        "type": "Avatar",
        "id": 91,
        "person_name": "Faker McFakeface",
        "pos": {"x": 15, "y": 27},
    }


@pytest.fixture(name="petless_person")
def petless_person_fixture():
    return {
        "type": "Avatar",
        "id": 81,
        "person_name": "Petless McPetface",
        "pos": {"x": 20, "y": 20},
    }


@pytest.fixture(name="available_pets")
def available_pets_fixture():
    return [
        {
            "type": "Bot",
            "id": pet_id,
            "name": pet["name"],
            "emoji": pet["emoji"],
            "pos": {"x": spawn_point[0], "y": spawn_point[1]},
        }
        for (pet_id, pet, spawn_point) in zip(itertools.count(800), PETS, SPAWN_POINTS)
    ]


@pytest.fixture(name="owned_cat")
def owned_cat_fixture(person):
    return {
        "type": "Bot",
        "id": 39887,
        "name": "Faker McFakeface's cat",
        "emoji": "🐈",
        "pos": {"x": 1, "y": 1},
        "message": {
            "mentioned_entity_ids": [person["id"]],
            "text": "@**Faker McFakeface** miaow!",
        },
    }


@pytest.fixture(name="in_day_care_unicorn")
def in_day_care_unicorn_fixture(person):
    return {
        "type": "Bot",
        "id": 987,
        "name": "Faker McFakeface's unicorn",
        "emoji": "🦄",
        "pos": {"x": 6, "y": 70},
        "message": {
            "mentioned_entity_ids": [person["id"]],
            "text": "@**Faker McFakeface** please don't forget about me!",
        },
    }


def incoming_message(sender, recipients, message, dt=0):
    if isinstance(recipients, dict):
        recipients = [recipients]
    recipients = [recipient["id"] for recipient in recipients]

    epoch_seconds = 2015491007  # Some time in 2033
    sent_at = datetime.utcfromtimestamp(epoch_seconds + dt).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    sender["message"] = {
        "mentioned_entity_ids": recipients,
        "sent_at": sent_at,
        "text": message,
    }
    return sender


@pytest.mark.asyncio
async def test_thanks(genie, person):
    session = MockSession({"bots": [genie]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(incoming_message(person, genie, "thanks!"))

    assert await session.message_received(genie, person) in THANKS_RESPONSES


@pytest.mark.asyncio
async def test_adopt_unavailable(genie, rocket, person):
    session = MockSession({"bots": [genie, rocket]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "adopt the dog, please!")
        )

    assert (
        await session.message_received(genie, person)
        == "Sorry, we don't have a dog at the moment, perhaps you'd like a rocket instead?"
    )


@pytest.mark.asyncio
async def test_successful_adoption(genie, rocket, person):
    session = MockSession({"bots": [genie, rocket]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "adopt the rocket, please!")
        )

    assert await session.message_received(rocket, person) == NOISES["🚀"]

    request = await session.get_request()

    assert request == Request(
        method="patch",
        path="bots",
        id=rocket["id"],
        json={"bot": {"name": f"{person['person_name']}'s rocket"}},
    )

    assert is_adjacent(person["pos"], await session.moved_to())


@pytest.mark.asyncio
async def test_successful_adopt_at_random(genie, rocket, person):
    session = MockSession({"bots": [genie, rocket]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "adopt a pet, please!")
        )

    assert await session.message_received(rocket, person) == NOISES["🚀"]

    request = await session.get_request()

    assert request == Request(
        method="patch",
        path="bots",
        id=rocket["id"],
        json={"bot": {"name": f"{person['person_name']}'s rocket"}},
    )

    assert is_adjacent(person["pos"], await session.moved_to())


@pytest.mark.asyncio
async def test_successful_seahorse_adoption(genie, rocket, person):
    session = MockSession({"bots": [genie, rocket]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "adopt a seahorse, please!")
        )

    assert await session.message_received(rocket, person) == NOISES["🚀"]

    request = await session.get_request()

    assert request == Request(
        method="patch",
        path="bots",
        id=rocket["id"],
        json={"bot": {"name": f"{person['person_name']}'s seahorse"}},
    )

    assert is_adjacent(person["pos"], await session.moved_to())


@pytest.mark.asyncio
async def test_successful_abandonment(genie, owned_cat, person):
    session = MockSession({"bots": [genie, owned_cat]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "I wish to heartlessly abandon my cat!")
        )

    assert await session.message_received(owned_cat, person) in [
        template.format(pet_name="cat") for template in SAD_MESSAGE_TEMPLATES
    ]

    request = await session.get_request()
    assert request == Request(
        method="delete", path="bots", id=owned_cat["id"], json=None
    )


@pytest.mark.asyncio
async def test_unsuccessful_abandonment(genie, owned_cat, person):
    session = MockSession({"bots": [genie, owned_cat]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "I wish to heartlessly abandon my owl!")
        )

    assert (
        await session.message_received(genie, person)
        == "Sorry, you don't have an owl. Would you like to abandon your cat instead?"
    )


@pytest.mark.asyncio
async def test_successful_day_care_drop_off(genie, owned_cat, person):
    session = MockSession({"bots": [genie, owned_cat]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "Please look after my cat!")
        )
        person["pos"] = {"x": 50, "y": 45}
        await agency.handle_entity(person)

    assert (
        await session.message_received(owned_cat, person)
        == "Please don't forget about me!"
    )

    assert await session.moved_to() in DAY_CARE_CENTER

    await asyncio.sleep(1)
    assert not session.pending_requests()


@pytest.mark.asyncio
async def test_unsuccessful_day_care_drop_off(genie, owned_cat, person):
    session = MockSession({"bots": [genie, owned_cat]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "Please look after my unicorn!")
        )

    assert (
        await session.message_received(genie, person)
        == "Sorry, you don't have a unicorn. Would you like to drop off your cat instead?"
    )


@pytest.mark.asyncio
async def test_successful_day_care_pick_up(genie, in_day_care_unicorn, person):
    session = MockSession({"bots": [genie, in_day_care_unicorn]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "Could I collect my unicorn, please?")
        )

    assert await session.message_received(in_day_care_unicorn, person) == "✨"

    assert is_adjacent(person["pos"], await session.moved_to())


@pytest.mark.asyncio
async def test_wrong_pet_day_care_pick_up(genie, in_day_care_unicorn, person):
    session = MockSession({"bots": [genie, in_day_care_unicorn]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "Could I collect my rocket, please?")
        )

    assert (
        await session.message_received(genie, person)
        == "Sorry, you don't have a rocket to collect. Would you like to collect your unicorn instead?"
    )


@pytest.mark.asyncio
async def test_day_care_pick_up_all_pets(genie, in_day_care_unicorn, person):
    session = MockSession({"bots": [genie, in_day_care_unicorn]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "Could I collect my all, please?")
        )

    assert await session.message_received(in_day_care_unicorn, person) == "✨"

    assert is_adjacent(person["pos"], await session.moved_to())


@pytest.mark.asyncio
async def test_follow_owner(genie, owned_cat, person):
    session = MockSession({"bots": [genie, owned_cat]})

    async with await Agency.create(session) as agency:
        person["pos"] = {"x": 50, "y": 45}
        await agency.handle_entity(person)

    assert is_adjacent(person["pos"], await session.moved_to())


@pytest.mark.asyncio
async def test_owner_changes_name(genie, owned_cat, person):
    session = MockSession({"bots": [genie, owned_cat]})

    async with await Agency.create(session) as agency:
        person["person_name"] = "Eve Newname"
        await agency.handle_entity(person)

    updated_pet = await session.moved_to()
    assert updated_pet["name"] == "Eve Newname's cat"


@pytest.mark.asyncio
async def test_owner_changes_name_back_again(genie, owned_cat, person):
    session = MockSession({"bots": [genie, owned_cat]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity({**owned_cat, "name": "Eve Newname's cat"})
        person["person_name"] = "Faker McFakeface"
        await agency.handle_entity(person)

    updated_pet = await session.moved_to()
    assert updated_pet["name"] == "Faker McFakeface's cat"


@pytest.mark.asyncio
async def test_owner_changes_name_during_day_care(genie, in_day_care_unicorn, person):
    session = MockSession({"bots": [genie, in_day_care_unicorn]})

    async with await Agency.create(session) as agency:
        person["person_name"] = "Eve Newname"
        await agency.handle_entity(person)

    updated_pet = await session.moved_to()
    assert updated_pet["name"] == "Eve Newname's unicorn"


@pytest.mark.asyncio
async def test_ignores_unrelated_other(genie, owned_cat):
    session = MockSession({"bots": [genie]})
    async with await Agency.create(session) as agency:
        await agency.handle_entity(owned_cat)


#
# TODO - Make versions of these tests that work.
#
# @pytest.mark.asyncio
# async def test_corral(owned_cat):
#     pet = pets.Pet(owned_cat)

#     assert pet.owner == 91

#     await pet.update({"x": 2, "y": 3})

#     updates = pet.queued_updates()
#     assert await updates.__anext__() == {"x": 2, "y": 3}

#     corral_move = await updates.__anext__()
#     assert corral_move in pets.CORRAL

#     await pet.update({"x": 8, "y": 9})
#     assert await updates.__anext__() == {"x": 8, "y": 9}

#     corral_move = await updates.__anext__()
#     assert corral_move in pets.CORRAL

#     await pet.update(None)
#     with pytest.raises(StopAsyncIteration):
#         await updates.__anext__()


# @pytest.mark.asyncio
# async def test_unowned_pets_dont_escape(rocket):
#     pet = pets.Pet(rocket)

#     assert pet.owner is None

#     await pet.update({"x": 2, "y": 3})

#     updates = pet.queued_updates()
#     assert await updates.__anext__() == {"x": 2, "y": 3}
#     await asyncio.sleep(1.5)

#     await pet.update({"x": 8, "y": 9})
#     assert await updates.__anext__() == {"x": 8, "y": 9}

#     await pet.update(None)
#     with pytest.raises(StopAsyncIteration):
#         await updates.__anext__()


@pytest.mark.asyncio
async def test_pet_a_pet(genie, owned_cat, petless_person, person):
    session = MockSession({"bots": [genie, owned_cat]})
    pets.lured.LURE_TIME_SECONDS = 600

    async with await Agency.create(session) as agency:
        petless_person["pos"] = {"x": 1, "y": 2}  # Cat is at 1,1 - this is adjacent.
        await agency.handle_entity(petless_person)
        await agency.handle_entity(
            incoming_message(petless_person, genie, "Pet the cat!")
        )
        petless_person["pos"] = {"x": 21, "y": 30}
        await agency.handle_entity(petless_person)

        # Rightful owner should be ignored
        person["pos"] = {"x": 99, "y": 99}
        await agency.handle_entity(person)

    pet_position = await session.moved_to()
    assert is_adjacent(petless_person["pos"], pet_position)


@pytest.mark.asyncio
async def test_pet_a_pet_with_pet_move(genie, owned_cat, petless_person, person):
    session = MockSession({"bots": [genie, owned_cat]})
    pets.lured.LURE_TIME_SECONDS = 600

    async with await Agency.create(session) as agency:
        await agency.handle_entity({**owned_cat, "pos": {"x": 99, "y": 108}})
        petless_person["pos"] = {
            "x": 100,
            "y": 108,
        }
        await agency.handle_entity(petless_person)
        await agency.handle_entity(
            incoming_message(petless_person, genie, "Pet the cat!")
        )
        petless_person["pos"] = {"x": 21, "y": 30}
        await agency.handle_entity(petless_person)

        # Rightful owner should be ignored
        person["pos"] = {"x": 99, "y": 99}
        await agency.handle_entity(person)

    pet_position = await session.moved_to()
    assert is_adjacent(petless_person["pos"], pet_position)


@pytest.mark.asyncio
async def test_pet_a_pet_expired(genie, owned_cat, petless_person, person):
    session = MockSession({"bots": [genie, owned_cat]})
    pets.lured.LURE_TIME_SECONDS = -1

    async with await Agency.create(session) as agency:
        petless_person["pos"] = {"x": 1, "y": 2}  # Cat is at 1,1 - this is adjacent.
        await agency.handle_entity(petless_person)
        await agency.handle_entity(
            incoming_message(petless_person, genie, "Pet the cat!")
        )
        petless_person["pos"] = {"x": 21, "y": 30}
        await agency.handle_entity(petless_person)

        # Rightful owner should not be ignored: timer is expired
        person["pos"] = {"x": 99, "y": 99}
        await agency.handle_entity(person)
        petless_person["pos"] = {"x": 21, "y": 30}
        await agency.handle_entity(petless_person)

    pet_position = await session.moved_to()
    assert is_adjacent(person["pos"], pet_position)


@pytest.mark.asyncio
async def test_restock_from_empty(genie, person):
    session = MockSession({"bots": [genie]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(incoming_message(person, genie, "Time to restock!"))

    assert len(agency.agency_sync.pet_directory.available()) == len(SPAWN_POINTS)
    assert await session.message_received(genie, person) == "New pets now in stock!"


@pytest.mark.asyncio
async def test_restock_partial(genie, person, available_pets):
    session = MockSession({"bots": [genie] + available_pets[:4]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(incoming_message(person, genie, "Time to restock!"))

    request = await session.get_request()
    assert request == Request(
        method="delete", path="bots", id=available_pets[0]["id"], json=None
    )
    assert (
        await session.message_received(genie, person)
        == "A bat was unwanted and has been sent to the farm."
    )

    assert len(agency.agency_sync.pet_directory.available()) == len(SPAWN_POINTS)
    assert await session.message_received(genie, person) == "New pets now in stock!"


@pytest.mark.asyncio
async def test_restock_full(genie, person, available_pets):
    session = MockSession({"bots": [genie] + available_pets})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(incoming_message(person, genie, "Time to restock!"))

    assert len(agency.agency_sync.pet_directory.available()) == len(SPAWN_POINTS)
    assert await session.message_received(genie, person) == "New pets now in stock!"


@pytest.mark.asyncio
async def test_successful_mystery_box_acquisition(genie, person):
    mystery_box = {
        "type": "Bot",
        "id": 5555,
        "name": "Mystery Box",
        "emoji": "🎁",
        "pos": {"x": MYSTERY_HOME["x"], "y": MYSTERY_HOME["y"]},
    }
    session = MockSession({"bots": [genie, mystery_box]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(person, genie, "adopt a surprise, please!")
        )

    # Pet should be renamed and emoji should be updated to the revealed pet
    request = await session.get_request()
    assert request.method == "patch"
    assert request.path == "bots"
    assert request.id == mystery_box["id"]
    bot_update = request.json["bot"]
    # Verify the emoji was changed from 🎁 to the revealed pet's emoji
    assert "emoji" in bot_update
    assert "name" in bot_update
    updated_pet = [pet for pet in PETS if pet["emoji"] == bot_update["emoji"]]
    assert bot_update["name"] == updated_pet[0]["name"]

    # Mystery box should send a message with the noise of the revealed pet
    message = await session.message_received(mystery_box, person)
    assert message in NOISES.values()

    # Pet should be renamed and emoji should be updated to the revealed pet
    request = await session.get_request()
    assert request.method == "patch"
    assert request.path == "bots"
    assert request.id == mystery_box["id"]
    bot_update = request.json["bot"]
    assert person["person_name"] in bot_update["name"]

    # Pet should move adjacent to person
    assert is_adjacent(person["pos"], await session.moved_to())


@pytest.mark.asyncio
async def test_successful_give_pet(genie, person, petless_person, owned_cat):
    session = MockSession({"bots": [genie, owned_cat]})

    async with await Agency.create(session) as agency:
        # Send preliminary message to make sure the agency knows about the recipient.
        await agency.handle_entity(
            incoming_message(
                petless_person, [person], "Hi, could I borrow your cat, please?"
            )
        )

        await agency.handle_entity(
            incoming_message(
                person,
                [genie, petless_person],
                "Give my cat to @**Petless Person**!",
                dt=2,
            )
        )

    assert (
        await session.message_received(owned_cat, petless_person)
        == NOISES[owned_cat["emoji"]]
    )
    request = await session.get_request()

    assert request == Request(
        method="patch",
        path="bots",
        id=owned_cat["id"],
        json={"bot": {"name": f"{petless_person['person_name']}'s cat"}},
    )

    assert is_adjacent(petless_person["pos"], await session.moved_to())


@pytest.mark.asyncio
async def test_unsuccessful_give_pet(genie, person, petless_person, owned_cat):
    session = MockSession({"bots": [genie, owned_cat]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(
            incoming_message(
                person,
                [genie, petless_person],
                "Give my owl to @**Petless Person**!",
            )
        )

    assert (
        await session.message_received(genie, person)
        == "Sorry, you don't have an owl. Would you like to give your cat instead?"
    )


@pytest.mark.asyncio
async def test_genie_autospawn():
    session = MockSession({"bots": []})

    async with await Agency.create(session) as agency:
        pass

    assert agency.agency_sync.genie.name == "Pet Agency Genie"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message,response",
    [
        ("help me!", HELP_TEXT),
        (
            "adopt the unicorn now, you stupid genie",
            "No please? Our pets are only available to polite homes.",
        ),
        (
            "adopt the unicorn, please",
            "Sorry, we don't have any pets at the moment, perhaps it's time to restock?",
        ),
        (
            "adopt the horse, please",
            "Sorry, that's just a picture of a horse.",
        ),
        ("adopt the genie, please", "You can't adopt me. I'm not a pet!"),
        (
            "adopt the apatosaurus, please",
            "Since 2015 the brontasaurus and apatosaurus have been recognised as separate species. Would you like to adopt a brontasaurus?",
        ),
        (
            "adopt a pet, please",
            "Sorry, we don't have any pets at the moment, perhaps it's time to restock?",
        ),
        (
            "fire rocket at my friends",
            "Sorry, I don't understand. Would you like to adopt a pet?",
        ),
        (
            "abandon my owl, please",
            "Sorry, you don't have any pets to abandon, perhaps you'd like to adopt one?",
        ),
        (
            "drop off my snail, please",
            "Sorry, you don't have any pets to drop off, perhaps you'd like to adopt one?",
        ),
        (
            "pick up my snail, please",
            "Sorry, you have no pets in day care. Would you like to drop one off?",
        ),
        ("That's a well-actually.", "Oh, you're right. Sorry!"),
        (
            "give my parrot to bob",
            "Sorry, you don't have any pets to give away, perhaps you'd like to adopt one?",
        ),
    ],
)
async def test_basic_messages_user_with_no_pets(
    genie, petless_person, owned_cat, message, response
):
    session = MockSession({"bots": [genie, owned_cat]})

    async with await Agency.create(session) as agency:
        await agency.handle_entity(incoming_message(petless_person, genie, message))

    assert await session.message_received(genie, petless_person) == response
