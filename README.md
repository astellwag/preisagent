# Preisagent

Checks prices on Thomann's (german) website and can send an email whenever a price drops

## Syntax

```usage: preisagent.py [-h] [-d] [-m MAIL]

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           enable debug output
  -m MAIL, --mail MAIL  send email to address```

## Configuration

The program requires a writeable directory "~/.preisagent" and a file "artikel.txt" inside. The format of the file is one item per line as follows:

User readable item name, item url relative to https://www.thomann.de/de/

e.g.

```Boss Katana Artist, boss_katana_artist_mkii
Laney Cub-Supertop, laney_cub_supertop```

## Sending mail

When invoked with parameter "-m MAIL", the tool will send an email from/to MAIL whenever the price drops. This requires a working SMTP server listening at localhost.
