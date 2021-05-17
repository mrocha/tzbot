import asyncio
import re
import sys

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from . import settings


class ChatStream(ABC):
    @abstractmethod
    async def read_command(self) -> Tuple[str, str, List[str]]:
        """Retrieves the next command from the stream"""

    @abstractmethod
    async def send_message(self, nick: str, msg: str) -> None:
        """Sends message to the stream"""


class StdioStream(ChatStream):
    def __init__(self, istream=sys.stdin, ostream=sys.stdout):
        self.istream, self.ostream = istream, ostream

    async def read_command(self) -> Tuple[str, str, List[str]]:
        line = await self._readline()

        while line and not self._is_command(line):
            line = await self._readline()

        if not line:
            raise EOFError()

        return self._parse_command(line)

    async def send_message(self, nick: str, msg: str) -> None:
        prefix = f"{nick}: " if settings.TAG_USER else ""
        await self._write(f"{prefix}{msg}\n")

    async def _readline(self) -> None:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.istream.readline)

    async def _write(self, msg: str) -> None:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.ostream.write, msg)

    def _is_command(self, line: str) -> bool:
        cmd_regex = r"[a-zA-Z]\w{0,31}: \s*(!timeat|!timepopularity) .+"
        return re.fullmatch(cmd_regex, line.strip()) is not None

    def _parse_command(self, line: str) -> Tuple[str, str, List[str]]:
        if not self._is_command(line):
            raise ValueError("invalid command message")

        nick, msg = line.split(": ", 1)
        cmd = msg.strip().split()
        cmd, args = cmd[0], cmd[1:]

        return nick, cmd, args
