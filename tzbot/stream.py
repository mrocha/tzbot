import asyncio
import logging
import re
import sys

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from . import settings

logger = logging.getLogger("tzbot")


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


class IRCStream(ChatStream):
    def __init__(self, server: str, port: int, nick: str, channel: str) -> None:
        self.server, self.port = server, port
        self.nick, self.channel = nick, channel
        self.istream = self.ostream = None

    async def connect(self) -> None:
        self.istream, self.ostream = await asyncio.open_connection(
            self.server, self.port
        )

        logger.debug(f"IRC: Joining channel {self.channel} as {self.nick}")
        self.ostream.writelines(
            [
                f"NICK {self.nick}\r\n".encode(),
                f"USER {self.nick} 0 * :{self.nick}\r\n".encode(),
                f"JOIN {self.channel}\r\n".encode(),
            ]
        )
        await self.ostream.drain()

    async def read_command(self) -> Tuple[str, str, List[str]]:
        while not self.istream.at_eof():
            try:
                line = await self.istream.readuntil(separator=b"\r\n")
            except asyncio.IncompleteReadError:
                self.ostream.close()
                raise EOFError()
            else:
                line = line[:-2].decode()
                if self._is_command(line):
                    return self._parse_command(line)
                if self._is_ping(line):
                    await self._pong(line)

        self.ostream.close()
        raise EOFError()

    async def send_message(self, nick: str, msg: str) -> None:
        prefix = f"{nick}: " if settings.TAG_USER else ""
        message = f"PRIVMSG {self.channel} :{prefix}{msg}\r\n"
        self.ostream.write(message.encode())
        await self.ostream.drain()

    def _is_command(self, line: str) -> bool:
        cmd_regex = r":\S+ PRIVMSG \S+ :\s*(!timeat|!timepopularity) .+"
        return re.fullmatch(cmd_regex, line) is not None

    def _parse_command(self, line: str) -> Tuple[str, str, List[str]]:
        logger.debug(f"IRC: parsing command '{line}'")
        cmd_regex = r":([^!]+)!\S+ PRIVMSG \S+ :\s*(!timeat|!timepopularity) (.+)"
        m = re.fullmatch(cmd_regex, line)
        return m[1], m[2], m[3].split()

    def _is_ping(self, line: str) -> bool:
        return re.fullmatch(r"PING .+", line) is not None

    async def _pong(self, line: str) -> None:
        m = re.fullmatch(r"PING (.+)", line)
        logger.debug(f"IRC: PONG {m[1]}")
        self.ostream.write(f"PONG {m[1]}".encode())
        await self.ostream.drain()
