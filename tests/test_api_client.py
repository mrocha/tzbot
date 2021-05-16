import aiohttp
import api_client as api
import pytest
import settings

from aiohttp import ClientSession
from datetime import datetime
from urllib.parse import urljoin


@pytest.mark.asyncio
async def test_should_return_datetime_when_successful(response, tztime):
    response.get(
        urljoin(settings.TIME_API, "/api/timezone/somewhere"),
        payload={"datetime": tztime.isoformat()},
        repeat=True,
    )

    async with ClientSession() as session:
        result = await api.get_time_at("somewhere", session)

    assert tztime == result


@pytest.mark.asyncio
async def test_should_raise_error_when_timezone_is_invalid(response):
    url = urljoin(settings.TIME_API, "/api/timezone/somewhere")
    error_msg = "unknown timezone"
    response.get(url, status=404, repeat=True)

    with pytest.raises(api.APIError, match=error_msg):
        async with ClientSession() as session:
            await api.get_time_at("somewhere", session)

    _, requests = response.requests.popitem()
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_should_retry_when_http_error(response):
    url = urljoin(settings.TIME_API, "/api/timezone/somewhere")
    error_msg = r"unable to retrieve time \(http code: 401\)"
    response.get(url, status=401, repeat=True)

    with pytest.raises(api.APIError, match=error_msg):
        async with ClientSession() as session:
            await api.get_time_at("somewhere", session)

    _, requests = response.requests.popitem()
    assert len(requests) == settings.BACKOFF_MAX_RETRIES


@pytest.mark.asyncio
async def test_should_retry_when_connection_error(response):
    url = urljoin(settings.TIME_API, "/api/timezone/somewhere")
    error_msg = "connection error"
    response.get(url, exception=aiohttp.ServerTimeoutError, repeat=True)

    with pytest.raises(api.APIError, match=error_msg):
        async with ClientSession() as session:
            await api.get_time_at("somewhere", session)

    _, requests = response.requests.popitem()
    assert len(requests) == settings.BACKOFF_MAX_RETRIES


@pytest.mark.asyncio
async def test_should_retry_when_invalid_json(response):
    url = urljoin(settings.TIME_API, "/api/timezone/somewhere")
    error_msg = "malformed response error"
    response.get(url, body=".", repeat=True)

    with pytest.raises(api.APIError, match=error_msg):
        async with ClientSession() as session:
            await api.get_time_at("somewhere", session)

    _, requests = response.requests.popitem()
    assert len(requests) == settings.BACKOFF_MAX_RETRIES


@pytest.mark.asyncio
async def test_should_retry_when_unexpected_error(response):
    url = urljoin(settings.TIME_API, "/api/timezone/somewhere")
    error_msg = "unknown error"
    response.get(url, exception=RuntimeError, repeat=True)

    with pytest.raises(api.APIError, match=error_msg):
        async with ClientSession() as session:
            await api.get_time_at("somewhere", session)

    _, requests = response.requests.popitem()
    assert len(requests) == settings.BACKOFF_MAX_RETRIES


@pytest.mark.asyncio
async def test_should_retry_when_time_is_missing(response):
    url = urljoin(settings.TIME_API, "/api/timezone/somewhere")
    error_msg = "time is unavailable"
    response.get(url, payload={}, repeat=True)

    with pytest.raises(api.APIError, match=error_msg):
        async with ClientSession() as session:
            await api.get_time_at("somewhere", session)

    _, requests = response.requests.popitem()
    assert len(requests) == settings.BACKOFF_MAX_RETRIES


@pytest.mark.asyncio
async def test_should_return_timezones(response):
    timezones = ["a", "b", "c"]
    response.get(
        urljoin(settings.TIME_API, "/api/timezone"), payload=timezones, repeat=True
    )

    async with ClientSession() as session:
        result = await api.get_timezones(session)

    assert timezones == result


@pytest.fixture(autouse=True)
def no_wait_between_retries(monkeypatch):
    monkeypatch.setattr(settings, "BACKOFF_INITIAL_WAIT", 0)
