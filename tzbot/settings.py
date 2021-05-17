from os import getenv


BACKOFF_INITIAL_WAIT = 1
BACKOFF_MAX_RETRIES = 4
POLL_FILENAME = "popularity_poll"
TAG_USER = False
TIME_API = getenv("TIME_API", default="https://worldtimeapi.org/")
