# Preisagent

Checks prices on Thomann's (german) website and can send an email whenever a price drops

## Syntax

```
usage: preisagent.py [-h] [-d] [-m MAIL]

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           enable debug output
  -m MAIL, --mail MAIL  send email to address
  -t Bot-ID Chat-ID, --telegram Bot-ID Chat-ID
                        send telegram message to bot-id chat-id
  -s Group-ID, --signal Group-ID
	                      send signal message to <Group-ID>
```

## Configuration

The program requires a writeable directory "~/.preisagent" and a file "preisagent.ini" inside. 

## Sending mail

When invoked with parameter "-m MAIL", the tool will send an email from/to MAIL whenever the price drops. This requires a working SMTP server listening at localhost.

## Telegram suppoort

When invoked with parameter -t BOT CHAT, it will send a telegram message using the bot wwith token BOT and chat-id CHAT.

## Signal suppoort

When invoked with parameter -s Group-ID, it will send a signal message to group Group_ID. This requires <https://github.com/AsamK/signal-cli> configured and running as a system-dbus service. For now, this uses the first accound configured with signal-cli.
