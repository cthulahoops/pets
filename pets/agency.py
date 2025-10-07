"""Async API wrapper for the pet agency."""

import asyncio
import datetime
import random

import rctogether

from .agency_sync import AgencySync
from .update_queues import UpdateQueues
from . import update_queues
from .constants import PET_BOREDOM_TIMES, CORRAL


def parse_dt(date_string):
    return datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)


async def reset_agency():
    async with rctogether.RestApiSession() as session:
        for bot in await rctogether.bots.get(session):
            if bot["emoji"] == "🧞":
                pass
            elif not bot.get("message"):
                print("Bot: ", bot)
                await rctogether.bots.delete(session, bot["id"])


class Agency:
    """
    public interface:
        create (static)
            (session) -> Agency
        handle_entity
            (json_blob)
    """

    def __init__(self, session):
        self.session = session
        self.processed_message_dt = datetime.datetime.now(datetime.timezone.utc)
        self.agency_sync = AgencySync()
        self._update_queues = UpdateQueues(self.queue_iterator)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    @classmethod
    async def create(cls, session):
        bots = await rctogether.bots.get(session)

        agency = cls(session)

        for event in agency.agency_sync.start(bots):
            await agency.apply_event(event)

        return agency

    async def queue_iterator(self, queue, pet_id):
        pet = self.agency_sync.pet_directory.get(pet_id)

        updates = update_queues.deduplicated_updates(queue)

        while True:
            next_update = asyncio.Task(updates.__anext__())
            while True:
                try:
                    update = await asyncio.wait_for(
                        asyncio.shield(next_update),
                        timeout=random.randint(*PET_BOREDOM_TIMES),
                    )
                    yield update
                    break
                except asyncio.TimeoutError:
                    if pet and pet.owner and not pet.is_in_day_care_center:
                        yield rctogether.bots.update(
                            self.session, pet.id, CORRAL.random_point()
                        )
                except StopAsyncIteration:
                    return

    async def close(self):
        await self._update_queues.close()

    async def handle_mention(self, adopter, message):
        mentioned_entity_ids = message["mentioned_entity_ids"]

        message_dt = parse_dt(message["sent_at"])
        if message_dt <= self.processed_message_dt:
            return
        self.processed_message_dt = message_dt

        for event in self.agency_sync.handle_mention(
            adopter, message, mentioned_entity_ids
        ):
            await self.apply_event(event)

    async def apply_event(self, event):
        match event[0]:
            case "send_message":
                recipient, message_text, sender = event[1:]
                await rctogether.messages.send(
                    self.session,
                    sender.id,
                    f"@**{recipient['person_name']}** {message_text}",
                )
            case "update_pet":
                pet, update = event[1:]
                await self._update_queues.add_task(
                    pet.id, rctogether.bots.update(self.session, pet.id, update)
                )
            case "sync_update_pet":
                await rctogether.bots.update(self.session, event[1].id, event[2])
            case "delete_pet":
                pet = event[1]
                await self._update_queues.add_task(pet.id, None)
                await rctogether.bots.delete(self.session, pet.id)
            case "create_pet":
                pet = await rctogether.bots.create(self.session, **event[1])
                self.agency_sync.handle_created(pet)
            case _:
                raise ValueError(f"Unknown event: {event}")

    async def handle_entity(self, entity):
        if entity["type"] == "Avatar":
            message = entity.get("message")
            if message:
                await self.handle_mention(entity, message)

            for event in self.agency_sync.handle_avatar(entity):
                await self.apply_event(event)

        if entity["type"] == "Bot":
            self.agency_sync.handle_bot(entity)
