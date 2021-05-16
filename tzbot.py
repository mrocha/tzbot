#!/usr/bin/env python3
import api_client as api
import asyncio
import json
import logging
import poll
import sys

from aiohttp import ClientSession
from datetime import datetime
from pathlib import Path
from signal import SIGINT, SIGTERM
from stream import ChatStream, StdioStream
from typing import Dict, List

logging.basicConfig(
    format="%(asctime)s [%(levelname)s -- %(filename)s(%(funcName)s:%(lineno)s)]: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("tzbot")

for m in ("charder.charsetprober", "selector_events"):
    logging.getLogger(m).setLevel(logging.CRITICAL)


class TZBot:
    r"""A basic IRC bot that tells the time on any timezone.

    The bot processes a message at a time per call to `process_msg()`.

    The bot is able to tell the time obtained from an external service
    through a REST API call and keep track of the number of valid
    `!timeat` requests received per timezone prefix.

    The bot's main loop preoccupies with dispatching new tasks for
    processing incoming commands. These tasks, once concluded, will
    write the message into the stream.

    Once EOF is reached, it waits for pending running tasks and exits.

    Arguments:

        stream -- A ChatStream object from where new commands can be
            read and messages written.
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

            logger.info(f"Bot ready to receive commands")
            while not self.eof:
                try:
                    nick, cmd, args = await self.stream.read_command()
                except EOFError:
                    self.eof = True
                else:
                    logger.info(f"Command received from '{nick}': {cmd} {args}")
                    tasks.append(
                        asyncio.create_task(self._process_cmd(nick, cmd, args))
                    )
                    # Filter out done tasks
                    tasks = [t for t in tasks if not t.done()]

            logger.info(f"EOF reached. Shutting down.")
            await asyncio.gather(*tasks)

    async def _process_cmd(self, nick: str, cmd: str, args: List[str]) -> None:
        """Fulfills a given command.

        Once the result for the command is obtained, it writes it
        into the stream. Non supported commands are ignored and no
        messages are sent.
        """
        message = None

        if cmd == "!timeat" and len(args) == 1:
            message = await self._timeat_cmd(args[0])
        elif cmd == "!timepopularity" and len(args) == 1:
            message = await self._timepopularity_cmd(args[0])

        if message:
            logger.info(f"Sending result for '{nick}': {message}")
            await self.stream.send_message(message)
        else:
            logger.info(f"Ignoring command from '{nick}': {cmd} {args}")

    async def _timeat_cmd(self, tz: str) -> str:
        """Implements the `!timeat <tzinfo>` command."""
        # If timezone is an alias, use the full timezone name
        if tz in self.aliases:
            tz = self.aliases[tz]

        try:
            tztime = await api.get_time_at(tz, self.session)
        except api.APIError as e:
            # Answer with error message
            logger.error(f"Couldn't retrieve time at {tz}: {str(e)}")
            return str(e)
        else:
            await poll.increment_popularity_of(tz)
            return self._format_time(tztime)

    def _format_time(self, tztime: datetime) -> str:
        return tztime.strftime("%-d %b %Y %H:%M")

    async def _timepopularity_cmd(self, tz_or_prefix):
        """Implements the `!timepopularity <tzinfo_or_prefix>` command."""
        return str(await poll.get_popularity_of(tz_or_prefix))

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
        logger.info("Execution was interrupted. Closing down.")
