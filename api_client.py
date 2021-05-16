import requests
import time
import utils
import settings

from datetime import datetime
from typing import Any, Callable
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
    """Makes a REST request to get the time at the given timezone."""
    if not utils.is_valid_timezone(timezone):
        return None

    url = urljoin(settings.TIME_API, f"/api/timezone/{timezone}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        json_response = response.json()
        return datetime.fromisoformat(json_response["datetime"])
    except requests.HTTPError:
        if response.status_code == 404:
            raise APIError("unknown timezone")
        else:
            raise RetriableError(
                f"unable to retrieve time (http code: {response.status_code})"
            )
    except (requests.ConnectionError, requests.Timeout):
        raise RetriableError("connection error")
    except Exception:
        # JSON decoding errors will be handled here as well
        raise RetriableError("unknown error")
