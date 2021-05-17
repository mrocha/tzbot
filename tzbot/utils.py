import asyncio
import importlib.resources as pkg_resources
import json
import re

from aiohttp import ClientSession

from . import api_client as api


def is_valid_timezone(timezone: str) -> bool:
    # Can only start or end with an alphanumeric character. Minimum size is 3
    return (
        re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9\+-_/]+[a-zA-Z0-9]", timezone) is not None
    )


def tz_prefixes(timezone: str) -> str:
    """Yields every prefix from a timezone delimited by '/'."""
    tokens = timezone.split("/")
    for i in range(len(tokens)):
        yield "/".join(tokens[: i + 1])


async def generate_aliases() -> None:
    """Generates the aliases JSON file."""
    # Retrieve all available timezones
    async with ClientSession() as session:
        try:
            timezones = await api.get_timezones(session)
        except api.APIError:
            timezones = []

    # Map each suffix with its timezone
    aliases = {tz.split("/")[-1]: tz for tz in timezones}

    # Validate each suffix is unique
    if len(aliases) != len(timezones):
        raise RuntimeError("conflicting aliases between timezones")

    # Dump the aliases over a JSON file
    with pkg_resources.path(__package__, "aliases.json") as path:
        with path.open("w") as f:
            f.write(json.dumps(aliases, indent=2))
