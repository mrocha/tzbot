import re
import sys

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class ChatStream(ABC):
    @property
    @abstractmethod
    def reader(self):
        """Stream from where messages are received."""

    @property
    @abstractmethod
    def writer(self):
        """Stream where messages are sent."""

    @abstractmethod
    def is_command(self, line: str) -> bool:
        """Validates a given string is a valid bot command."""

    @abstractmethod
    def parse_command(self, line: str) -> Tuple[str, str, List[str]]:
        """Extracts nickname, command and arguments from a string."""


class StdioStream(ChatStream):
    @property
    def reader(self):
        return sys.stdin

    @property
    def reader(self):
        return sys.stdio

    def is_command(self, line: str) -> bool:
        cmd_regex = r"[a-zA-Z]\w{0,31}: \s*(!timeat|!timepopularity) .+"
        return re.fullmatch(cmd_regex, line.strip()) is not None

    def parse_command(self, line: str) -> Tuple[str, str, List[str]]:
        if not self.is_command(line):
            raise ValueError("invalid command message")

        nick, msg = line.split(": ", 1)
        cmd = msg.strip().split()
        cmd, args = cmd[0], cmd[1:]

        return nick, cmd, args
