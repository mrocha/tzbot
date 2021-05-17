from os import getenv


BACKOFF_INITIAL_WAIT = 1
BACKOFF_MAX_RETRIES = 4

TAG_USER = False
POLL_FILENAME = "popularity_poll"
TIME_API = getenv("TIME_API", default="https://worldtimeapi.org/")

IRC_SERVER = "chat.freenode.net"
IRC_PORT = 6667
IRC_NICK = "el_tzbot"
IRC_CHANNEL = "##mrocha"
