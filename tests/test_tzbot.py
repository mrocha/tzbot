import api_client as api
import pytest
import settings

from io import StringIO
from pathlib import Path
from stream import StdioStream
from tzbot import TZBot


def test_should_return_time_when_given_valid_timezone(
    mocker, bot, tztime, formatted_tztime
):
    mocker.patch("api_client.get_time_at", return_value=tztime)
    send_message(bot, "josh: !timeat America/Chicago")

    bot.process_msg()

    assert formatted_tztime == recv_message(bot)


def test_should_return_time_when_given_an_aliased_timezone(
    mocker, bot, tztime, formatted_tztime
):
    mock = mocker.patch("api_client.get_time_at", return_value=tztime)
    send_message(bot, "josh: !timeat Vancouver")

    bot.process_msg()

    assert formatted_tztime == recv_message(bot)
    mock.assert_called_with("America/Vancouver")


def test_should_return_error_when_given_invalid_timezone(
    mocker, bot, tztime, formatted_tztime
):
    mocker.patch("api_client.get_time_at", side_effect=api.APIError("unknown timezone"))
    send_message(bot, "josh: !timeat Somewhere")

    bot.process_msg()

    assert "unknown timezone\n" == recv_message(bot)


def test_should_ignore_non_command_messages(bot):
    send_message(bot, "josh: something")
    bot.process_msg()
    assert "" == recv_message(bot)


def test_should_return_popularity_when_given_a_timezone(mocker, bot, tztime):
    mocker.patch("api_client.get_time_at", return_value=tztime)
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
    send_messages(bot, messages)

    for _ in range(len(messages)):
        bot.process_msg()

    responses = recv_messages(bot, len(messages))[3:]
    assert "2\n" == responses[0]
    assert "1\n" == responses[1]
    assert "1\n" == responses[2]
    assert "1\n" == responses[3]
    assert "1\n" == responses[4]
    assert "0\n" == responses[5]


def test_should_not_update_counter_for_invalid_timezones(mocker, bot):
    mocker.patch("api_client.get_time_at", side_effect=api.APIError("unknown timezone"))
    messages = [
        "josh: !timeat Somewhere",
        "josh: !timepopularity Somewhere",
    ]
    send_messages(bot, messages)

    for _ in range(len(messages)):
        bot.process_msg()

    responses = recv_messages(bot, len(messages))

    assert "unknown timezone\n" == responses[0]
    assert "0\n" == responses[1]


def test_should_update_counter_for_aliased_timezones(
    mocker, bot, tztime, formatted_tztime
):
    mock = mocker.patch("api_client.get_time_at", return_value=tztime)
    messages = [
        "josh: !timeat Vancouver",
        "josh: !timepopularity America",
    ]
    send_messages(bot, messages)

    for _ in range(len(messages)):
        bot.process_msg()

    responses = recv_messages(bot, len(messages))

    assert formatted_tztime == responses[0]
    mock.assert_called_with("America/Vancouver")
    assert "1\n" == responses[1]


class MockStream(StdioStream):
    def __init__(self):
        self.streams = StringIO(), StringIO()

    @property
    def reader(self):
        return self.streams[0]

    @property
    def writer(self):
        return self.streams[1]


@pytest.fixture
def bot():
    return TZBot(MockStream())


def send_message(bot, msg):
    return send_messages(bot, [msg])


def send_messages(bot, msgs):
    for msg in msgs:
        bot.stream.reader.write(msg + "\n")
    bot.stream.reader.seek(0)


def recv_message(bot):
    return recv_messages(bot, 1)[0]


def recv_messages(bot, amount):
    msgs = []
    bot.stream.writer.seek(0)
    for _ in range(amount):
        msgs.append(bot.stream.writer.readline())
    return msgs


@pytest.fixture(autouse=True)
def change_and_delete_poll_file(monkeypatch):
    monkeypatch.setattr(settings, "POLL_FILENAME", "test_poll")
    for path in Path(".").glob(f"{settings.POLL_FILENAME}*"):
        path.unlink()
