import pytest

from aiohttp import ClientSession
from io import StringIO
from pathlib import Path
from tzbot import api_client as api
from tzbot import settings
from tzbot import TZBot
from tzbot.stream import StdioStream


@pytest.mark.asyncio
async def test_should_return_time_when_given_valid_timezone(
    mocker, bot, tztime, formatted_tztime, stream
):
    mocker.patch("tzbot.api_client.get_time_at", return_value=tztime)
    send_message(stream, bot, "josh: !timeat America/Chicago")

    await bot.run()

    assert formatted_tztime == recv_message(stream, bot)


@pytest.mark.asyncio
async def test_should_return_time_when_given_an_aliased_timezone(
    mocker, bot, tztime, formatted_tztime, stream
):
    mock = mocker.patch("tzbot.api_client.get_time_at", return_value=tztime)
    send_message(stream, bot, "josh: !timeat Vancouver")

    await bot.run()

    assert formatted_tztime == recv_message(stream, bot)
    assert mock.call_args.args[0] == "America/Vancouver"


@pytest.mark.asyncio
async def test_should_return_error_when_given_invalid_timezone(
    mocker, bot, tztime, formatted_tztime, stream
):
    mocker.patch(
        "tzbot.api_client.get_time_at", side_effect=api.APIError("unknown timezone")
    )
    send_message(stream, bot, "josh: !timeat Somewhere")

    await bot.run()

    assert "unknown timezone\n" == recv_message(stream, bot)


@pytest.mark.asyncio
async def test_should_ignore_non_command_messages(bot, stream):
    send_message(stream, bot, "josh: something")
    await bot.run()
    assert "" == recv_message(stream, bot)


@pytest.mark.asyncio
async def test_should_return_popularity_when_given_a_timezone(
    mocker, bot, tztime, stream
):
    mocker.patch("tzbot.api_client.get_time_at", return_value=tztime)
    messages = [
        "josh: !timeat America/Chicago",
        "josh: !timeat America/Argentina/Buenos_Aires",
        "josh: !timeat Etc/GMT+10",
        "josh: !timepopularity America",
        "josh: !timepopularity America/Chicago",
        "josh: !timepopularity America/Argentina",
        "josh: !timepopularity Etc",
        "josh: !timepopularity Etc/GMT+10",
        "josh: !timepopularity SomewhereElse",
    ]
    send_messages(stream, bot, messages)

    await bot.run()

    responses = recv_messages(stream, bot, len(messages))[3:]
    assert "2\n" == responses[0]
    assert "1\n" == responses[1]
    assert "1\n" == responses[2]
    assert "1\n" == responses[3]
    assert "1\n" == responses[4]
    assert "0\n" == responses[5]


@pytest.mark.asyncio
async def test_should_not_update_counter_for_invalid_timezones(mocker, bot, stream):
    mocker.patch(
        "tzbot.api_client.get_time_at", side_effect=api.APIError("unknown timezone")
    )
    messages = [
        "josh: !timeat Somewhere",
        "josh: !timepopularity Somewhere",
    ]
    send_messages(stream, bot, messages)

    await bot.run()

    responses = recv_messages(stream, bot, len(messages))

    assert "unknown timezone\n" == responses[0]
    assert "0\n" == responses[1]


@pytest.mark.asyncio
async def test_should_update_counter_for_aliased_timezones(
    mocker, bot, tztime, formatted_tztime, stream
):
    mock = mocker.patch("tzbot.api_client.get_time_at", return_value=tztime)
    messages = [
        "josh: !timeat Vancouver",
        "josh: !timepopularity America",
    ]
    send_messages(stream, bot, messages)

    await bot.run()

    responses = recv_messages(stream, bot, len(messages))

    assert formatted_tztime == responses[0]
    assert mock.call_args.args[0] == "America/Vancouver"
    assert "1\n" == responses[1]


class MockStream(StdioStream):
    def __init__(self):
        super().__init__(StringIO(), StringIO())


@pytest.fixture
def stream():
    return MockStream()


@pytest.fixture
def bot(stream):
    return TZBot(stream)


def send_message(stream, bot, msg):
    return send_messages(stream, bot, [msg])


def send_messages(stream, bot, msgs):
    for msg in msgs:
        stream.istream.write(msg + "\n")
    stream.istream.seek(0)


def recv_message(stream, bot):
    return recv_messages(stream, bot, 1)[0]


def recv_messages(stream, bot, amount):
    msgs = []
    stream.ostream.seek(0)
    for _ in range(amount):
        msgs.append(stream.ostream.readline())
    return msgs


@pytest.fixture(autouse=True)
def change_and_delete_poll_file(monkeypatch):
    monkeypatch.setattr(settings, "POLL_FILENAME", "test_poll")
    for path in Path(".").glob(f"{settings.POLL_FILENAME}*"):
        path.unlink()
