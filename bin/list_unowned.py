import argparse
import asyncio
from collections import defaultdict
import rctogether


async def fetch_live_data():
    async with rctogether.RestApiSession() as session:
        return await rctogether.bots.get(session)


async def delete_bot(session, bot_id):
    await rctogether.bots.delete(session, bot_id)


async def cleanup_overlapping(pets_to_delete, dry_run=True):
    if dry_run:
        print("\n[DRY RUN] Would delete the following bots:")
        for pet in pets_to_delete:
            name = pet.get("name", "Unknown")
            emoji = pet.get("emoji", "?")
            pos = pet.get("pos", {})
            x = pos.get("x", "?")
            y = pos.get("y", "?")
            pet_id = pet.get("id", "?")
            print(f"  {name:<20} {emoji:<10} ({x}, {y}){'':<7} {pet_id}")
        print(f"\n[DRY RUN] Total: {len(pets_to_delete)} bots would be deleted")
    else:
        async with rctogether.RestApiSession() as session:
            for pet in pets_to_delete:
                name = pet.get("name", "Unknown")
                pet_id = pet.get("id", "?")
                print(f"Deleting {name} (ID: {pet_id})...")
                await delete_bot(session, pet_id)
        print(f"\nDeleted {len(pets_to_delete)} bots")


def main():
    parser = argparse.ArgumentParser(
        description="List all unowned pets (pets that have never sent a message)"
    )
    parser.add_argument(
        "file", nargs="?", help="JSON file to read (if not provided, fetches live data)"
    )
    parser.add_argument(
        "--cleanup-overlapping",
        action="store_true",
        help="Delete overlapping unowned bots (keeps the oldest at each position)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show what would be deleted without actually deleting (default: True)",
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Actually perform the deletion (disables dry-run)",
    )
    args = parser.parse_args()

    dry_run = args.dry_run and not args.no_dry_run

    data = asyncio.run(fetch_live_data())

    unowned_pets = [bot for bot in data if not bot.get("message")]
    unowned_pets = [pet for pet in unowned_pets if pet.get("emoji") != "🧞"]

    if args.cleanup_overlapping:
        position_map = defaultdict(list)
        for pet in unowned_pets:
            pos = pet.get("pos", {})
            x = pos.get("x")
            y = pos.get("y")
            if x is not None and y is not None:
                position_map[(x, y)].append(pet)

        pets_to_delete = []
        for pos, pets_at_pos in position_map.items():
            if len(pets_at_pos) > 1:
                sorted_pets = sorted(pets_at_pos, key=lambda p: p.get("id", 0))
                pets_to_delete.extend(sorted_pets[1:])

        if pets_to_delete:
            print(f"Found {len(pets_to_delete)} overlapping unowned bots")
            asyncio.run(cleanup_overlapping(pets_to_delete, dry_run=dry_run))
        else:
            print("No overlapping unowned bots found")
    else:
        print(f"Found {len(unowned_pets)} unowned pets:\n")
        print(f"{'Name':<20} {'Emoji':<10} {'Position':<15} {'ID'}")
        print("-" * 65)

        for pet in sorted(unowned_pets, key=lambda p: p.get("name", "")):
            name = pet.get("name", "Unknown")
            emoji = pet.get("emoji", "?")
            pos = pet.get("pos", {})
            x = pos.get("x", "?")
            y = pos.get("y", "?")
            pet_id = pet.get("id", "?")
            print(f"{name:<20} {emoji:<10} ({x}, {y}){'':<7} {pet_id}")


if __name__ == "__main__":
    main()
