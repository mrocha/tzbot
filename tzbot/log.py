import logging
import sys


def setup_logger(name):
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s -- %(filename)s(%(funcName)s:%(lineno)s)]: %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    return logging.getLogger("tzbot")
