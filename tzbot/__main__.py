import asyncio

from signal import SIGINT, SIGTERM

from . import log
from . import TZBot
from .stream import StdioStream, IRCStream

logger = log.setup_logger("tzbot")


async def async_entry_point():
    loop = asyncio.get_running_loop()
    task = asyncio.current_task()

    for signal in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal, task.cancel)

    irc = IRCStream("chat.freenode.net", 6667, "el_tzbot", "##mrocha")
    await irc.connect()

    bot = TZBot(irc)
    await bot.run()


def main():
    try:
        asyncio.run(async_entry_point())
    except asyncio.CancelledError:
        logger.info("Execution was interrupted. Closing down.")


if __name__ == "__main__":
    main()
