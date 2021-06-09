#!/usr/bin/python3

import sys
import argparse
import requests
import json
import re
from urllib.request import urlopen
from smtplib import SMTP
from email.message import EmailMessage
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action="store_true", help="enable debug output")
parser.add_argument("-m", "--mail", help="send email to address")
parser.add_argument("-t", "--telegram", 
	help="send telegram message to bot-id chat-id",
	nargs=2,
	metavar=("Bot-ID", "Chat-ID") )
args = parser.parse_args()

mailtxt="""\
Hi,

der Preis für %s ist gefallen.

Alter Preis: %d
Neuer Preis: %d

Link zum Artikel: %s

Cheers,
Dein Preisagent
"""

home = str(Path.home())
confdir = home + '/.preisagent/'
listfile = confdir + 'preisagent.ini'

mode = "none"
shops = {}
articles = {}

# read configfile
with open(listfile) as c:
	lines = c.readlines()

for l in lines:
	line = l.strip()
	if line == "[shops]":
		mode = "shops"
		regex = r"(\w+)_(\w+)\s+=\s+(.*)"
		continue
	elif re.match("\[(.*)\]", line):
		match = re.match("\[(.*)\]", line)
		name = match.group(1)
		mode = match.group(1).lower().replace(" ","_")
		regex = r"url_(\w+)\s+=\s+(.*)"
		continue
	
	if mode == "none": continue
	
	elif mode == "shops":
		if re.search(regex, line):
			match = re.search(regex, line)
			key = match.group(2)
			if not key in shops: shops[key] = {}
			shops[key][match.group(1)] = match.group(3)

	elif re.search(regex, line):
		match = re.search(regex, line)
		if not mode in articles:
			articles[mode] = {}
			articles[mode]['name'] = name
			articles[mode]['shops'] = {}
		articles[mode]['shops'][match.group(1)] = match.group(2)


for art in articles:
	a = articles[art]
	if args.debug:
		print(a['name'])
		print("=======================================")

	# alten Preis lesen
	filename = confdir + a['name'].lower().replace(' ', '_')
	if args.debug:
		print(f"Trying to open {filename}")
	try:
		with open(filename) as f:
			preisline = f.readlines()[0].strip().split(':')
			if args.debug: print(preisline)
			oldshop = preisline[0]
			oldpreis = float(preisline[1])
	except IOError:
			oldshop = ''
			oldpreis = 99999999999.9

	lshop = oldshop
	lpreis = oldpreis
	if args.debug:
		print(lshop + ': ' + str(lpreis))

	for sho in a['shops']:
		s = shops[sho]
		url = s['baseurl'] + a['shops'][sho] + s['append']
		if args.debug:
			print(url)
			print(s['matchre'])
		html = urlopen(url).read().decode("UTF-8")
		if re.search(s['matchre'], html):
			if args.debug:
				print("match")
				print(re.search(s['matchre'], html).group(1))
			p = re.search(s['matchre'], html).group(1)
			if p.find(","):
				preis = float(p.replace(",","."))
			else:
				preis = float(p)
			
			if preis < lpreis:
				lshop = s['name']
				lpreis = preis

	if args.debug:			
		print( a['name'] + " ist bei " + lshop + " am günstigsten: " + str(lpreis) + "€")

	# neuen günstigsten Preis speichern
	if lpreis < oldpreis or lshop != oldshop:
		if args.debug:
			print("Storing new price")
		with open(filename, "w") as f:
			f.write(lshop + ':' + str(lpreis) + "\n")
		
		# send email
		if args.mail:
			if args.debug:
				print("Sending eMail")
			msg = EmailMessage()
			msg.set_content(mailtxt % (a['name'], oldpreis, lpreis, url))
			msg['Subject'] = "Neuer Preis für %s: %.2f" % (a['name'], lpreis)
			msg['From'] = args.mail
			msg['To'] = args.mail
	
			s = SMTP('localhost')
			s.send_message(msg)
			s.quit()

		# send telegram message
		if args.telegram:
			if args.debug:
				print("Sending Telegram Message")
				
			params = {"chat_id":args.telegram[1], "text":f"Neuer Preis für {a['name']}: {lpreis}€\n{url}"}
			message = requests.post(f"https://api.telegram.org/bot{args.telegram[0]}/sendMessage", params=params)

			if args.debug:
				print(message)
		


# vim: set ts=4:
