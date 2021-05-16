import asyncio
import settings
import shelve
import utils


async def increment_popularity_of(timezone: str) -> None:
    """Updates the number of requests received for every prefix of timezone."""

    def blocking_func():
        with shelve.open(settings.POLL_FILENAME) as poll:
            for prefix in utils.tz_prefixes(timezone):
                if prefix not in poll:
                    poll[prefix] = 0
                poll[prefix] += 1

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, blocking_func)


async def get_popularity_of(timezone: str) -> int:
    """Retrieves the number of requests received for timezones with the given prefix."""

    def blocking_func():
        with shelve.open(settings.POLL_FILENAME) as poll:
            return poll[timezone] if timezone in poll else 0

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, blocking_func)
