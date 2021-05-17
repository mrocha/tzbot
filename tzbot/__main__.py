import argparse
import asyncio

from signal import SIGINT, SIGTERM

from . import log, settings, TZBot, utils
from .stream import StdioStream, IRCStream

logger = log.setup_logger("tzbot")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tzbot", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--irc", action="store_true", help="Serves requests from IRC instead of STDIO"
    )
    parser.add_argument(
        "--aliases",
        action="store_true",
        help="Generates and rewrites the aliases JSON file. Then exits",
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="If enabled, bot tags the requesting user on response",
    )
    parser.add_argument(
        "--time-api",
        help="Time API URL. This takes precedence over the environment variable",
        default=settings.TIME_API,
    )
    parser.add_argument(
        "--irc-server", help="IRC server to connect to", default=settings.IRC_SERVER
    )
    parser.add_argument(
        "--irc-channel", help="IRC channel to join to", default=settings.IRC_CHANNEL
    )

    return parser.parse_args()


def update_settings(args: argparse.Namespace) -> None:
    settings.TAG_USER = args.tag
    settings.TIME_API = args.time_api
    settings.IRC_SERVER = args.irc_server
    settings.IRC_CHANNEL = args.irc_channel


def register_signal_handlers() -> None:
    loop = asyncio.get_running_loop()
    task = asyncio.current_task()

    for signal in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal, task.cancel)


async def async_entry_point() -> None:
    args = parse_args()

    if args.aliases:
        logger.info("Generating aliases.json file...")
        await utils.generate_aliases()
        return

    update_settings(args)
    register_signal_handlers()

    if args.irc:
        stream = IRCStream(
            settings.IRC_SERVER,
            settings.IRC_PORT,
            settings.IRC_NICK,
            settings.IRC_CHANNEL,
        )
        await stream.connect()
    else:
        stream = StdioStream()

    bot = TZBot(stream)
    await bot.run()


def main() -> None:
    try:
        asyncio.run(async_entry_point())
    except asyncio.CancelledError:
        logger.info("Execution was interrupted. Closing down.")


if __name__ == "__main__":
    main()
