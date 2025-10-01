import argparse
import asyncio
import json
from collections import Counter
import rctogether


async def fetch_live_data():
    async with rctogether.RestApiSession() as session:
        return await rctogether.bots.get(session)


def main():
    parser = argparse.ArgumentParser(description="Show pet leaderboard")
    parser.add_argument("file", nargs="?", help="JSON file to read (if not provided, fetches live data)")
    args = parser.parse_args()

    if args.file:
        # Read from file
        with open(args.file) as f:
            data = json.load(f)
    else:
        # No argument, fetch live data
        data = asyncio.run(fetch_live_data())

    counts = Counter(x["name"].split("'")[0] for x in data)

    name_to_emojis = {}
    for pet in data:
        name = pet["name"].split("'")[0]
        if name not in name_to_emojis:
            name_to_emojis[name] = []
        name_to_emojis[name].append(pet.get("emoji", "🐾"))

    print("Top 10 Leaderboard:")
    print("-" * 60)
    for i, (name, count) in enumerate(counts.most_common(10), 1):
        emojis = "".join(name_to_emojis.get(name, ["🐾"]))
        print(f"{i:2d}. {name:20s} {count:5d} {emojis}")


if __name__ == "__main__":
    main()
