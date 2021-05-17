# TZBot

TZBot is a simple IRC bot that can tell the time at any timezone.

## Installation

```bash
python3 -m venv venv
. venv/bin/activate
python setup.py install
```

## Usage

```bash
$ tzbot --help
usage: tzbot [-h] [--irc] [--aliases] [--tag] [--time-api TIME_API] [--irc-server IRC_SERVER] [--irc-channel IRC_CHANNEL]

optional arguments:
  -h, --help            show this help message and exit
  --irc                 Serves requests from IRC instead of STDIO (default: False)
  --aliases             Generates and rewrites the aliases JSON file. Then exits (default: False)
  --tag                 If enabled, bot tags the requesting user on response (default: False)
  --time-api TIME_API   Time API URL. This takes precedence over the environment variable (default: https://worldtimeapi.org/)
  --irc-server IRC_SERVER
                        IRC server to connect to (default: chat.freenode.net)
  --irc-channel IRC_CHANNEL
                        IRC channel to join to (default: ##mrocha)
```

## Testing

```bash
. venv/bin/activate
pip install -U tox
tox
```
