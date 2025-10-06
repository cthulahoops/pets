"""Synchronous game logic engine for the pet agency."""

import random

from .pet import Pet, owned_pet_name
from .pet_directory import PetDirectory
from .lured import Lured
from .parser import parse_command
from .geometry import offset_position, is_adjacent, DELTAS
from .constants import (
    GENIE_NAME,
    GENIE_EMOJI,
    GENIE_HOME,
    MYSTERY_HOME,
    MANNERS,
    PETS,
    NOISES,
    HELP_TEXT,
    SAD_MESSAGE_TEMPLATES,
    THANKS_RESPONSES,
    DAY_CARE_CENTER,
)


def sad_message(pet_name):
    return random.choice(SAD_MESSAGE_TEMPLATES).format(pet_name=pet_name)


def a_an(noun):
    if noun == "unicorn":
        return "a " + noun
    if noun[0] in "AaEeIiOoUu":
        return "an " + noun
    return "a " + noun


def upfirst(text):
    return text[0].upper() + text[1:]


def get_one_by_type(pet_type, pets):
    return next(iter(pet for pet in pets if pet_type == pet.type), None)


class AgencySync:
    def __init__(self):
        self.pet_directory = PetDirectory()
        self.genie = None
        self.lured = Lured()
        self.avatars = {}
        self.genie = None

    def start(self, bots):
        for bot_json in bots:
            self.handle_created(bot_json)

        if not self.genie:
            yield (
                "create_pet",
                {
                    "name": GENIE_NAME,
                    "emoji": "🧞",
                    "x": GENIE_HOME["x"],
                    "y": GENIE_HOME["y"],
                    "can_be_mentioned": True,
                },
            )

        if not self.pet_directory.mystery_pets:
            yield (
                "create_pet",
                {
                    "name": "Mystery Box",
                    "emoji": "🎁",
                    "x": MYSTERY_HOME["x"],
                    "y": MYSTERY_HOME["y"],
                    "can_be_mentioned": False,
                },
            )

    def handle_help(self, adopter):
        return HELP_TEXT

    def handle_adoption(self, adopter, text, pet_type):
        if not any(please in text.lower() for please in MANNERS):
            yield "No please? Our pets are only available to polite homes."
            return

        if pet_type == "horse":
            yield "Sorry, that's just a picture of a horse."
            return

        if pet_type == "genie":
            yield "You can't adopt me. I'm not a pet!"
            return

        if pet_type == "apatosaurus":
            yield "Since 2015 the brontasaurus and apatosaurus have been recognised as separate species. Would you like to adopt a brontasaurus?"
            return

        if pet_type == "surprise" or pet_type == "mystery":
            if not self.pet_directory.mystery_pets:
                yield "Sorry, we don't have any mystery boxes at the moment."
                return
            pet = self.pet_directory.mystery_pets.pop()

            revealed_pet_type = random.choice(PETS)
            pet.bot_json["emoji"] = revealed_pet_type["emoji"]
            pet.bot_json["name"] = revealed_pet_type["name"]

            yield (
                "sync_update_pet",
                pet,
                {
                    "name": revealed_pet_type["name"],
                    "emoji": revealed_pet_type["emoji"],
                },
            )

            yield (
                "create_pet",
                {
                    "name": "Mystery Box",
                    "emoji": "🎁",
                    "x": MYSTERY_HOME["x"],
                    "y": MYSTERY_HOME["y"],
                    "can_be_mentioned": False,
                },
            )
        elif pet_type == "pet":
            try:
                pet = random.choice(list(self.pet_directory.available()))
            except IndexError:
                yield "Sorry, we don't have any pets at the moment, perhaps it's time to restock?"
                return
        else:
            pet = get_one_by_type(pet_type, self.pet_directory.available())

        if not pet:
            try:
                alternative = random.choice(list(self.pet_directory.available())).name
            except IndexError:
                yield "Sorry, we don't have any pets at the moment, perhaps it's time to restock?"
                return

            yield f"Sorry, we don't have {a_an(pet_type)} at the moment, perhaps you'd like {a_an(alternative)} instead?"
            return

        self.pet_directory.set_owner(pet, adopter)

        yield ("send_message", adopter, NOISES.get(pet.emoji, "💖"), pet)
        yield ("sync_update_pet", pet, {"name": owned_pet_name(adopter, pet.type)})

    def handle_abandon(self, adopter, pet_type):
        owned_pets = self.pet_directory.owned(adopter["id"])
        pet = get_one_by_type(pet_type, owned_pets)

        if not pet:
            if not owned_pets:
                return "Sorry, you don't have any pets to abandon, perhaps you'd like to adopt one?"
            suggested_alternative = random.choice(owned_pets).type
            return f"Sorry, you don't have {a_an(pet_type)}. Would you like to abandon your {suggested_alternative} instead?"

        self.pet_directory.remove(pet)

        return [
            ("send_message", adopter, sad_message(pet_type), pet),
            ("delete_pet", pet),
        ]

    def handle_thanks(self, adopter):
        return random.choice(THANKS_RESPONSES)

    def handle_social_rules(self, adopter):
        return "Oh, you're right. Sorry!"

    def handle_pet_a_pet(self, petter, pet_type):
        # For the moment this command needs to be addressed to the genie (maybe won't later).
        # Find any pets next to the speaker of the right type.
        #  Do we have any pets of the right type next to the speaker?
        for pet in self.pet_directory.all_owned():
            if is_adjacent(petter["pos"], pet.pos) and pet.type == pet_type:
                self.lured.add(pet, petter)

        return []

    def handle_give_pet(self, giver, pet_type, mentioned_entities):
        owned_pets = self.pet_directory.owned(giver["id"])
        pet = get_one_by_type(pet_type, owned_pets)

        if not pet:
            if not owned_pets:
                return "Sorry, you don't have any pets to give away, perhaps you'd like to adopt one?"

            suggested_alternative = random.choice(owned_pets).type

            return f"Sorry, you don't have {a_an(pet_type)}. Would you like to give your {suggested_alternative} instead?"

        if not mentioned_entities:
            return f"Who to you want to give your {pet_type} to?"
        recipient = self.avatars.get(mentioned_entities[0])

        if not recipient:
            return "Sorry, I don't know who that is! (Are they online?)"

        self.pet_directory.set_owner(pet, recipient)
        position = offset_position(recipient["pos"], random.choice(DELTAS))

        return [
            ("send_message", recipient, NOISES.get(pet.emoji, "💖"), pet),
            ("sync_update_pet", pet, {"name": owned_pet_name(recipient, pet.type)}),
            ("update_pet", pet, position),
        ]

    def handle_day_care_drop_off(self, owner, pet_type):
        pets_not_in_day_care = [
            pet
            for pet in self.pet_directory.owned(owner["id"])
            if not pet.is_in_day_care_center
        ]

        if pet_type in ("all", "pets"):
            events = []
            for pet in pets_not_in_day_care:
                pet.is_in_day_care_center = True
                position = DAY_CARE_CENTER.random_point()
                events.append(
                    ("send_message", owner, "Please don't forget about me!", pet)
                )
                events.append(("update_pet", pet, position))
            if not events:
                return "Sorry, you don't have any pets to drop off, perhaps you'd like to adopt one?"
            return events

        pet = get_one_by_type(pet_type, pets_not_in_day_care)

        if not pet:
            if not pets_not_in_day_care:
                return "Sorry, you don't have any pets to drop off, perhaps you'd like to adopt one?"
            suggested_alternative = random.choice(pets_not_in_day_care).type
            return f"Sorry, you don't have {a_an(pet_type)}. Would you like to drop off your {suggested_alternative} instead?"

        position = DAY_CARE_CENTER.random_point()
        pet.is_in_day_care_center = True

        return [
            ("send_message", owner, "Please don't forget about me!", pet),
            ("update_pet", pet, position),
        ]
        return None

    def handle_day_care_pick_up(self, owner, pet_type):
        pets_in_day_care = [
            pet
            for pet in self.pet_directory.owned(owner["id"])
            if pet.is_in_day_care_center
        ]

        if pet_type in ("all", "pets"):
            events = []
            for pet in pets_in_day_care:
                pet.is_in_day_care_center = False
                events.append(("send_message", owner, NOISES.get(pet.emoji, "💖"), pet))
            if not events:
                return "Sorry, you have no pets in day care. Would you like to drop one off?"
            return events

        pet = get_one_by_type(pet_type, pets_in_day_care)

        if not pet:
            if not pets_in_day_care:
                return "Sorry, you have no pets in day care. Would you like to drop one off?"
            suggested_alternative = random.choice(pets_in_day_care).type
            return f"Sorry, you don't have {a_an(pet_type)} to collect. Would you like to collect your {suggested_alternative} instead?"

        pet.is_in_day_care_center = False

        return [
            ("send_message", owner, NOISES.get(pet.emoji, "💖"), pet),
        ]

    def handle_avatar(self, entity):
        self.avatars[entity["id"]] = entity

        for pet in self.lured.get_by_petter(entity["id"]):
            position = offset_position(entity["pos"], random.choice(DELTAS))
            yield ("update_pet", pet, position)

        for pet in self.pet_directory.owned(entity["id"]):
            if pet.is_in_day_care_center or self.lured.check(pet):
                pet_update = {}
            else:
                pet_update = offset_position(entity["pos"], random.choice(DELTAS))

            # Handle possible name change.
            pet_name = owned_pet_name(entity, pet.type)
            if pet.name != pet_name:
                pet_update["name"] = pet_name

            if pet_update:
                yield ("update_pet", pet, pet_update)

    def handle_restock(self, restocker):
        if self.pet_directory.empty_spawn_points():
            pet = min(
                self.pet_directory.available(), key=lambda pet: pet.id, default=None
            )
            if pet:
                self.pet_directory.remove(pet)
                yield ("delete_pet", pet)
                yield f"{upfirst(a_an(pet.type))} was unwanted and has been sent to the farm."

        for pos in self.pet_directory.empty_spawn_points():
            pet = random.choice(PETS)
            while any(x.emoji == pet["emoji"] for x in self.pet_directory.available()):
                pet = random.choice(PETS)

            pet = {
                "name": pet["name"],
                "emoji": pet["emoji"],
                "x": pos[0],
                "y": pos[1],
                "can_be_mentioned": False,
            }
            yield ("create_pet", pet)
        yield "New pets now in stock!"

    def handle_created(self, pet_json):
        pet = Pet(pet_json)
        if pet.emoji == GENIE_EMOJI:
            print("Found the genie: ", pet_json)
            self.genie = pet
        else:
            self.pet_directory.add(pet)

    def handle_bot(self, entity):
        try:
            pet = self.pet_directory[entity["id"]]
        except KeyError:
            pass
        else:
            pet.pos = entity["pos"]
            pet.bot_json["name"] = entity["name"]

    def handle_command(self, adopter, text, mentioned_entities):
        parsed = parse_command(text)

        if not parsed:
            return "Sorry, I don't understand. Would you like to adopt a pet?"

        command, groups = parsed

        handler = getattr(self, f"handle_{command}")
        if command == "give_pet":
            return handler(
                adopter,
                groups[0],
                [
                    entity_id
                    for entity_id in mentioned_entities
                    if entity_id != self.genie.id
                ],
            )
        return handler(adopter, *groups)

    def handle_mention(self, adopter, message, mentioned_entity_ids):
        if self.genie.id not in mentioned_entity_ids:
            return

        events = self.handle_command(adopter, message["text"], mentioned_entity_ids)

        if isinstance(events, str):
            events = [events]

        for event in events:
            if isinstance(event, str):
                event = ("send_message", adopter, event, self.genie)

            yield event
