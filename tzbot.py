#!/usr/bin/env python3
import api_client as api
import re
import settings
import shelve
import sys
import utils

from datetime import datetime
from io import TextIOBase
from typing import List, Optional


class TZBot:
    def __init__(self, istream: TextIOBase, ostream: TextIOBase) -> None:
        self.istream = istream
        self.ostream = ostream

    def process_msg(self) -> None:
        nick, msg = self._receive_msg()
        if result := self._process_cmd(nick, msg):
            self._send_msg(result)

    def _receive_msg(self) -> List[str]:
        line = self.istream.readline()
        while not self._is_a_message(line):
            line = self.istream.readline()
        return self._parse_msg(line)

    def _send_msg(self, result: str) -> None:
        self.ostream.write(f"{result}\n")

    def _is_a_message(self, line: str) -> bool:
        nick, _ = self._parse_msg(line)
        return self._is_valid_nick(nick) if nick else False

    def _parse_msg(self, line: str) -> List[Optional[str]]:
        return line.split(": ", 1) if ": " in line else [None, None]

    def _is_valid_nick(self, nick: str) -> bool:
        return re.fullmatch(r"[a-zA-Z0-9]{1,32}", nick) is not None

    def _process_cmd(self, nick: str, msg: str) -> Optional[str]:
        cmd = msg.strip().split()
        cmd, args = cmd[:1], cmd[1:]

        # Ignore messages that are not commands
        if not cmd or (cmd := cmd[0])[0] != "!":
            return None

        # !timeat <tzinfo>
        if cmd == "!timeat" and len(args) == 1:
            try:
                tztime = api.get_time_at(args[0])
            except api.APIError as e:
                return str(e)
            else:
                self._increment_popularity_of(args[0])
                return self._format_time(tztime)

        # !timepopularity <tzinfo_or_prefix>
        elif cmd == "!timepopularity" and len(args) == 1:
            return str(self._get_popularity_of(args[0]))

        return None

    def _format_time(self, tztime: datetime) -> str:
        return tztime.strftime("%-d %b %Y %H:%M")

    def _increment_popularity_of(self, timezone: str) -> None:
        with shelve.open(settings.POLL_FILENAME) as poll:
            for prefix in utils.tz_prefixes(timezone):
                if prefix not in poll:
                    poll[prefix] = 0
                poll[prefix] += 1

    def _get_popularity_of(self, timezone: str) -> int:
        with shelve.open(settings.POLL_FILENAME) as poll:
            return poll[timezone] if timezone in poll else 0


if __name__ == "__main__":
    bot = TZBot(sys.stdin, sys.stdout)
    while True:
        bot.process_msg()
