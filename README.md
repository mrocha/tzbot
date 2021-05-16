# TZBot

TZBot is a lean IRC bot that can tell the time in any requested timezone.

## Installation

To create the virtual environment, install dependencies and generate the aliases map, execute:

```bash
make
```

## Usage

```bash
make run
```

## Assumptions

```
 Input takes the form of <username>: <message>, for example, josh: hello. There will always be exactly
 one space between the username - if there are multiple spaces, N-1 of them were part of the user’s message.
 The bot will receive a copy of all messages sent to the channel, but only needs to respond to those which start
 with an exclamation point, which we call “commands” - for example josh: !timeat America/Los_Angeles
```

 * For the MVP, input and output will be handled through stdio and files. The final version can handle IRC channels.
 * Usernames can only have alphanumeric characters, otherwise the message will be ignored.
 * I arbitrarily chose 32 as the maximum length a nickname can have.
 * If there are multiple spaces between username and message, then N-1 spaces will always show up after the colon.
 * Commands with leading spaces will be processed.
