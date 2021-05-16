import json
import requests
import time
import utils
import settings

from datetime import datetime
from typing import Any, Callable, Dict, List
from urllib.parse import urljoin


class APIError(RuntimeError):
    """An API error occurred."""


class RetriableError(RuntimeError):
    """A retriable error occurred."""


def backoff(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for exponential backoff retries."""

    def wrapper(*args, **kwargs) -> Any:
        retries = settings.BACKOFF_MAX_RETRIES
        delay = settings.BACKOFF_INITIAL_WAIT
        step = 2
        last_error = None

        while retries > 0:
            try:
                return func(*args, **kwargs)
            except RetriableError as e:
                last_error = e
                time.sleep(delay)
                delay *= step
                retries -= 1

        raise APIError(str(last_error))

    return wrapper


@backoff
def get_time_at(timezone: str) -> datetime:
    """Makes a request to get the time at the given timezone."""
    if not utils.is_valid_timezone(timezone):
        return None

    response = _make_call(f"/api/timezone/{timezone}")

    try:
        return datetime.fromisoformat(response.get("datetime", ""))
    except ValueError:
        raise RetriableError("time is unavailable")


@backoff
def get_timezones() -> List[str]:
    """Makes a request to retrieve all available timezones."""
    return _make_call(f"/api/timezone")


def _make_call(path: str) -> Dict[str, Any]:
    """Makes a REST GET request to the `TIME_API` service."""
    url = urljoin(settings.TIME_API, path)

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError:
        if response.status_code == 404:
            raise APIError("unknown timezone")
        else:
            raise RetriableError(
                f"unable to retrieve time (http code: {response.status_code})"
            )
    except (requests.ConnectionError, requests.Timeout):
        raise RetriableError("connection error")
    except json.decoder.JSONDecodeError:
        raise RetriableError("malformed response error")
    except Exception:
        raise RetriableError("unknown error")
