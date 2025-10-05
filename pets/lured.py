"""Lure tracking for pets."""

import time
from collections import defaultdict


LURE_TIME_SECONDS = 600


class Lured:
    def __init__(self):
        self.pets = {}
        self.by_petter = defaultdict(list)

    def add(self, pet, petter):
        # Use module-level variable to allow tests to modify the value
        self.pets[pet.id] = time.time() + LURE_TIME_SECONDS
        self.by_petter[petter["id"]].append(pet)

    def check(self, pet):
        if pet.id not in self.pets:
            return False

        if self.pets[pet.id] < time.time():  # if timer is expired
            del self.pets[pet.id]
            for petter_id in self.by_petter:
                for lured_pet in self.by_petter[petter_id]:
                    if lured_pet.id == pet.id:
                        self.by_petter[petter_id].remove(lured_pet)
            return False

        return True

    def get_by_petter(self, petter_id):
        return self.by_petter.get(petter_id, [])
