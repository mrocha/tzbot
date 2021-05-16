#!/usr/bin/env python3
import api_client as api
import json
import re
import settings
import shelve
import signal
import sys
import utils

from datetime import datetime
from io import TextIOBase
from typing import Dict, List, Optional


class TZBot:
    r"""A basic IRC bot that tells the time on any timezone.

    The bot processes a message at a time per call to `process_msg()`.

    The bot is able to tell the time obtained from an external service
    through a REST API call and keeps track of the number of valid
    `!timeat` requests received per timezone prefix.

    Arguments:

        istream -- Input stream where messages will be read from. Each
            message is defined as a newline ('\n') terminated string.

        ostream -- Output stream where the response to a command will
            be written. Each posted message ends with a newline.
    """

    def __init__(self, istream: TextIOBase, ostream: TextIOBase) -> None:
        self.istream = istream
        self.ostream = ostream
        self.ready = True
        self.aliases = self._load_aliases()

    def process_msg(self) -> None:
        """Processes the next message in the input stream."""
        try:
            nick, msg = self._receive_msg()
        except EOFError:
            self.ready = False
        else:
            if result := self._process_cmd(nick, msg):
                self._send_msg(result)

    def _receive_msg(self) -> List[str]:
        """Reads and validate a message from the input stream.

        When the streams reaches to EOF, it raises an EOFError."""

        line = self.istream.readline()

        while line and not self._is_a_message(line):
            line = self.istream.readline()

        if not line:
            raise EOFError()

        return self._parse_msg(line)

    def _send_msg(self, result: str) -> None:
        """Writes a message to the output stream."""
        self.ostream.write(f"{result}\n")

    def _is_a_message(self, line: str) -> bool:
        """Validates whether a string is a message."""
        nick, _ = self._parse_msg(line)
        return self._is_valid_nick(nick) if nick else False

    def _parse_msg(self, line: str) -> List[Optional[str]]:
        """Parses nickname and message from a string."""
        return line.split(": ", 1) if ": " in line else [None, None]

    def _is_valid_nick(self, nick: str) -> bool:
        """Validates whether a string is a valid nickname."""
        return re.fullmatch(r"[a-zA-Z0-9]{1,32}", nick) is not None

    def _process_cmd(self, nick: str, msg: str) -> Optional[str]:
        """Fulfills a command if it's present in the message.

        It returns the response message for the requested command.
        It returns `None` when there is no message to be sent."""

        cmd = msg.strip().split()
        cmd, args = cmd[:1], cmd[1:]

        # Ignore messages that are not commands
        if not cmd or (cmd := cmd[0])[0] != "!":
            return None

        if cmd == "!timeat" and len(args) == 1:
            return self._timeat_cmd(args[0])
        elif cmd == "!timepopularity" and len(args) == 1:
            return self._timepopularity_cmd(args[0])

        return None

    def _timeat_cmd(self, tz: str) -> str:
        """Implements the `!timeat <tzinfo>` command."""
        # If timezone is an alias, use the full timezone name
        if tz in self.aliases:
            tz = self.aliases[tz]

        try:
            tztime = api.get_time_at(tz)
        except api.APIError as e:
            # Answer with error message
            return str(e)
        else:
            self._increment_popularity_of(tz)
            return self._format_time(tztime)

    def _format_time(self, tztime: datetime) -> str:
        return tztime.strftime("%-d %b %Y %H:%M")

    def _increment_popularity_of(self, timezone: str) -> None:
        """Updates the number of requests received for every prefix of timezone."""
        with shelve.open(settings.POLL_FILENAME) as poll:
            for prefix in utils.tz_prefixes(timezone):
                if prefix not in poll:
                    poll[prefix] = 0
                poll[prefix] += 1

    def _timepopularity_cmd(self, tz_or_prefix):
        """Implements the `!timepopularity <tzinfo_or_prefix>` command."""
        return str(self._get_popularity_of(tz_or_prefix))

    def _get_popularity_of(self, timezone: str) -> int:
        """Retrieves the number of requests received for timezones with the given prefix."""
        with shelve.open(settings.POLL_FILENAME) as poll:
            return poll[timezone] if timezone in poll else 0

    def _load_aliases(self) -> Dict[str, str]:
        """Loads the aliases map from the pre-generated JSON file."""
        with open("aliases.json") as f:
            return json.load(f)


if __name__ == "__main__":

    def signal_handler(signal, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    bot = TZBot(sys.stdin, sys.stdout)
    while bot.ready:
        bot.process_msg()
