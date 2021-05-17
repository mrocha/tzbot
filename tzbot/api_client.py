import aiohttp
import asyncio
import json

from aiohttp import ClientSession
from datetime import datetime
from typing import Any, Callable, Dict, List
from urllib.parse import urljoin

from . import utils
from . import settings


class APIError(RuntimeError):
    """An API error occurred."""


class RetriableError(RuntimeError):
    """A retriable error occurred."""


def backoff(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for exponential backoff retries."""

    async def wrapper(*args, **kwargs) -> Any:
        retries = settings.BACKOFF_MAX_RETRIES
        delay = settings.BACKOFF_INITIAL_WAIT
        step = 2
        last_error = None

        while retries > 0:
            try:
                return await func(*args, **kwargs)
            except RetriableError as e:
                last_error = e
                await asyncio.sleep(delay)
                delay *= step
                retries -= 1

        raise APIError(str(last_error))

    return wrapper


@backoff
async def get_time_at(timezone: str, session: ClientSession) -> datetime:
    """Makes a request to get the time at the given timezone."""
    if not utils.is_valid_timezone(timezone):
        return None

    response = await _make_call(f"/api/timezone/{timezone}", session)

    try:
        return datetime.fromisoformat(response.get("datetime", ""))
    except ValueError:
        raise RetriableError("time is unavailable")


@backoff
async def get_timezones(session: ClientSession) -> List[str]:
    """Makes a request to retrieve all available timezones."""
    return await _make_call(f"/api/timezone", session)


async def _make_call(path: str, session: ClientSession) -> Dict[str, Any]:
    """Makes a REST GET request to the `TIME_API` service."""
    url = urljoin(settings.TIME_API, path)

    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    except (aiohttp.ContentTypeError, json.decoder.JSONDecodeError):
        raise RetriableError("malformed response error")
    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            raise APIError("unknown timezone")
        else:
            raise RetriableError(f"unable to retrieve time (http code: {e.status})")
    except aiohttp.ClientConnectionError:
        raise RetriableError("connection error")
    except Exception:
        raise RetriableError("unknown error")
