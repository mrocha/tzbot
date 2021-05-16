import re


def is_valid_timezone(timezone: str) -> bool:
    # Can only start or end with an alphanumeric character. Minimum size is 3
    return (
        re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9\+-_/]+[a-zA-Z0-9]", timezone) is not None
    )


def tz_prefixes(timezone: str) -> str:
    tokens = timezone.split("/")
    for i in range(len(tokens)):
        yield "/".join(tokens[: i + 1])
