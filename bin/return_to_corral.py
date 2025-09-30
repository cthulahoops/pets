#!/usr/bin/env python3
"""Return all owned pets to the corral."""

import argparse
import asyncio

import rctogether
from pets import CORRAL, GENIE_EMOJI

RATE_LIMITING_DELAY = 0.1
MAX_RETRIES = 5


async def main(dry_run=False):
    async with rctogether.RestApiSession() as session:
        bots = await rctogether.bots.get(session)

        owned_pets = [
            bot
            for bot in bots
            if is_owned(bot)
            and not is_in_day_care(bot)
            and not is_in_corral(bot)
            and not is_genie(bot)
        ]

        print(f"Found {len(owned_pets)} owned pets to move")

        if dry_run:
            print("DRY RUN - no pets will be moved")

        # Move each owned pet to a random point in the corral
        moved_count = 0
        for pet in owned_pets:
            if not dry_run:
                for attempt in range(MAX_RETRIES):
                    corral_position = CORRAL.random_point()
                    try:
                        print(f"Moving {pet['name']} to corral at {corral_position}")
                        await rctogether.bots.update(
                            session, pet["id"], corral_position
                        )
                        await asyncio.sleep(RATE_LIMITING_DELAY)
                        break
                    except rctogether.api.HttpError as e:
                        if e.args[0] == 422 and "must not be in a block" in e.args[1]:
                            print(
                                f"  Position blocked, retrying... (attempt {attempt + 1}/{MAX_RETRIES})"
                            )
                            if attempt == MAX_RETRIES - 1:
                                print(
                                    f"  Failed to move {pet['name']} after {MAX_RETRIES} attempts"
                                )
                            continue
                        else:
                            raise
            else:
                corral_position = CORRAL.random_point()
                print(f"Moving {pet['name']} to corral at {corral_position}")
            moved_count += 1

        if dry_run:
            print(f"DRY RUN complete - would have moved {moved_count} pets")
        else:
            print(f"All {moved_count} owned pets returned to corral")


def is_owned(bot):
    return bot.get("message") and bot["message"].get("mentioned_entity_ids")


def is_in_day_care(bot):
    return "forget" in bot.get("message", {}).get("text", "")


def is_in_corral(bot):
    return bot.get("pos") in CORRAL


def is_genie(bot):
    return bot.get("emoji") == GENIE_EMOJI


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Return all owned pets to the corral")
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without making changes",
    )
    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run))
