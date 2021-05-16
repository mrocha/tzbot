#!/usr/bin/env python3
import asyncio
import api_client as api
import json

from aiohttp import ClientSession


async def main():
    # Retrieve all available timezones
    async with ClientSession() as session:
        try:
            timezones = await api.get_timezones(session)
        except api.APIError:
            timezones = []

    # Map each suffix with its timezone
    aliases = {tz.split("/")[-1]: tz for tz in timezones}

    # Validate each suffix is unique
    assert len(aliases) == len(timezones)

    # Dump the aliases into a JSON file
    with open("aliases.json", "w") as f:
        f.write(json.dumps(aliases, indent=2))

asyncio.run(main())
