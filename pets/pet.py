"""Pet model for the pets module."""


class Pet:
    def __init__(self, bot_json, *a, **k):
        self.bot_json = bot_json
        self.pos = bot_json["pos"]
        self.is_in_day_care_center = False
        if bot_json.get("message"):
            self.owner = bot_json["message"]["mentioned_entity_ids"][0]
            if "forget" in bot_json["message"]["text"]:
                self.is_in_day_care_center = True
        else:
            self.owner = None

    @property
    def type(self):
        return self.name.split(" ")[-1]

    @property
    def id(self):
        return self.bot_json["id"]

    @property
    def emoji(self):
        return self.bot_json["emoji"]

    @property
    def name(self):
        return self.bot_json["name"]


def owned_pet_name(owner, pet_type):
    return f"{owner['person_name']}'s {pet_type}"
