import pytest

from aiohttp import ClientSession
from aioresponses import aioresponses
from datetime import datetime


@pytest.fixture
def tztime() -> datetime:
    return datetime.fromisoformat("2021-05-15T22:54:27")


@pytest.fixture
def formatted_tztime(tztime) -> datetime:
    return tztime.strftime("%-d %b %Y %H:%M") + "\n"


@pytest.fixture
def response():
    with aioresponses() as m:
        yield m
