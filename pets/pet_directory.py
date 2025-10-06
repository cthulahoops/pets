"""Pet registry and directory management."""

from collections import defaultdict
from .geometry import position_tuple


# Spawn points are defined in config, but we need to import them
# This will be set after config is created
SPAWN_POINTS = None


class PetDirectory:
    def __init__(self):
        self._available_pets = {}
        self.mystery_pets = []
        self._owned_pets = defaultdict(list)
        self._pets_by_id = {}

    def add(self, pet):
        self._pets_by_id[pet.id] = pet

        if pet.owner:
            self._owned_pets[pet.owner].append(pet)
        elif pet.emoji == "🎁":
            self.mystery_pets.append(pet)
        else:
            self._available_pets[position_tuple(pet.pos)] = pet

    def remove(self, pet):
        del self._pets_by_id[pet.id]

        if pet.owner:
            self._owned_pets[pet.owner].remove(pet)
        elif pet in self.mystery_pets:
            # Mystery pet - remove from mystery_pets list
            self.mystery_pets.remove(pet)
        else:
            # Available pet - remove from position-indexed dict
            pos_key = position_tuple(pet.pos)
            if pos_key in self._available_pets:
                del self._available_pets[pos_key]

    def available(self):
        return self._available_pets.values()

    def empty_spawn_points(self):
        # Import at runtime to avoid circular dependency
        from .constants import SPAWN_POINTS

        return SPAWN_POINTS - set(self._available_pets.keys())

    def owned(self, owner_id):
        return self._owned_pets[owner_id]

    def __iter__(self):
        for pet in self._available_pets.values():
            yield pet

        yield from self.all_owned()

    def all_owned(self):
        for pet_collection in self._owned_pets.values():
            for pet in pet_collection:
                yield pet

    def __getitem__(self, pet_id):
        return self._pets_by_id[pet_id]

    def get(self, pet_id, default=None):
        return self._pets_by_id.get(pet_id, default)

    def set_owner(self, pet, owner):
        self.remove(pet)
        pet.owner = owner["id"]
        self.add(pet)
