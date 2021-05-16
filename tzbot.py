#!/usr/bin/env python3
import api_client as api
import asyncio
import json
import settings
import shelve
import sys
import utils

from aiohttp import ClientSession
from datetime import datetime
from io import TextIOBase
from pathlib import Path
from signal import SIGINT, SIGTERM
from stream import ChatStream, StdioStream
from typing import Dict, List, Optional, Tuple


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

    def __init__(self, stream: ChatStream) -> None:
        self.stream = stream
        self.eof = False
        self.aliases = self._load_aliases()

    async def run(self) -> None:
        """Process every message in stream until EOF."""
        async with ClientSession() as session:
            self.session = session
            tasks = []

            while not self.eof:
                try:
                    nick, cmd, args = await self.stream.read_command()
                except EOFError:
                    self.eof = True
                else:
                    tasks.append(asyncio.create_task(self._process_cmd(nick, cmd, args)))
                    # Filter out done tasks
                    tasks = [t for t in tasks if not t.done()]

            await asyncio.gather(*tasks)

    async def _send_msg(self, result: str) -> None:
        """Writes a message to the output stream."""
        await self.stream.writer.write(f"{result}\n")

    async def _process_cmd(self, nick: str, cmd: str, args: List[str]) -> Optional[str]:
        """Fulfills a command if it's present in the message.

        It returns the response message for the requested command.
        It returns `None` when there is no message to be sent.
        """
        message = None

        if cmd == "!timeat" and len(args) == 1:
            message = await self._timeat_cmd(args[0])
        elif cmd == "!timepopularity" and len(args) == 1:
            message = self._timepopularity_cmd(args[0])

        if message:
            await self.stream.send_message(message)

    async def _timeat_cmd(self, tz: str) -> str:
        """Implements the `!timeat <tzinfo>` command."""
        # If timezone is an alias, use the full timezone name
        if tz in self.aliases:
            tz = self.aliases[tz]

        try:
            tztime = await api.get_time_at(tz, self.session)
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
        if not Path("aliases.json").exists():
            return {}
        with open("aliases.json") as f:
            return json.load(f)


async def main():
    loop = asyncio.get_running_loop()
    task = asyncio.current_task()

    for signal in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal, task.cancel)

    bot = TZBot(StdioStream())
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        pass
