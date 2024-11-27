#!/usr/bin/python3

import argparse
import asyncio
import json
import re
import requests
import sys
import urllib.request
from base64 import b64decode
from datetime import datetime
from email.message import EmailMessage
from nio import AsyncClient, MatrixRoom, RoomMessageText
from pathlib import Path
from pydbus import SystemBus
from smtplib import SMTP
from time import sleep
from urllib.error import URLError, HTTPError

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose output")
parser.add_argument("-d", "--debug", action="store_true", help="enable detailed debug output")
parser.add_argument("-e", "--email",
	help="send email to address",
	nargs=1,
	metavar=("Mail-address") )
parser.add_argument("-t", "--telegram", 
	help="send telegram message to <Bot-ID> <Chat-ID>",
	nargs=2,
	metavar=("Bot-ID", "Chat-ID") )
parser.add_argument("-m", "--matrix", 
	help="send matrix message to <server> <room>, use <user> and <pw> to login",
	nargs=4,
	metavar=("server", "room", "user", "password") )
parser.add_argument("-s", "--signal",
	help="send signal message to <Group-ID>",
	nargs=1,
	metavar=("Group-ID") )
parser.add_argument("-p", "--pause",
	help="pause <PAUSE> seconds after each call",
	nargs=1,
	type=int,
	metavar=("PAUSE") )
args = parser.parse_args()

if args.debug: args.verbose = True

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
if args.debug: print(f"Reading config file: {listfile}")

with open(listfile) as c:
	lines = c.readlines()

for l in lines:
	line = l.strip()

	if re.match("^#.*", line): continue

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
	if args.verbose:
		print(a['name'])
		print("=======================================")

	# alten Preis lesen
	filename = confdir + re.sub(r"[/ ]", "_", a['name']).lower()
	if args.debug:
		print(f"Trying to open {filename}")
	try:
		with open(filename) as f:
			preisline = f.readlines()[0].strip().split(':')
			if args.debug: print(preisline)
			oldshop = preisline[0]
			oldpreis = float(preisline[1])
			if args.debug:
				print(f"Alter Preis: {oldpreis}€ bei {oldshop}")
	except IOError:
			oldshop = ''
			oldpreis = 999999.9
			if args.debug: print("Alter Preis: ---")

	lurl = ''
	lshop = oldshop
	lpreis = 999999.9

	if args.debug:
		print(lshop + ': ' + str(lpreis))

	for sho in a['shops']:
		s = shops[sho]
		url = s['baseurl'] + a['shops'][sho]
		if 'append' in s: url = url + s['append']
		
		if args.debug:
			print(url)
			print(s['matchre'])
		try:
			req = urllib.request.Request(
				url,
				data=None,
				headers={
					'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
				}
			)
			html = urllib.request.urlopen(req).read().decode("UTF-8")
		except URLError as e:
			if hasattr(e, 'reason'):
				print(f"URL {url} unreachable: {e.reason}")
			elif hasattr(e, 'code'):
				print(f"HTTP request for {url} failed: {e.code}")
			continue
		except HTTPError as e:
			printf(f"HTTP error {e.code}")
			continue

		if 'match' in s:
			matchno = int(s['match'])-1
		else:
			matchno = 0
		if re.search(s['matchre'], html):
			if args.debug: print("searching for skip")
			if 'skip' in s:
				if re.search(s['skip'], html):
					if args.debug: print("Skipping")
					continue

			p = re.findall(s['matchre'], html)[matchno]
			if args.debug:
				print("match")
				print(re.findall(s['matchre'], html))
				print(p)
			if p.find(","):
				preis = float(p.replace(",","."))
			else:
				preis = float(p)
			if 'tax' in s:
				preis = round(preis * float(s['tax']), 2)
			
			if args.verbose:
				print(f"Preis bei {s['name']}: {preis}€")

			if preis < lpreis:
				lshop = s['name']
				lpreis = preis
				lurl = url

	if args.debug:			
		print( a['name'] + " ist bei " + lshop + " am günstigsten: " + str(lpreis) + "€")
	if args.verbose: print()

	# neuen Preis speichern
	if lpreis != oldpreis or lshop != oldshop:
		if args.debug:
			print("Storing new price")
		with open(filename, "w") as f:
			f.write(lshop + ':' + str(lpreis) + ":" + datetime.now().strftime("%Y-%m-%d") + "\n")
		
		# wenn neuer Preis < alter Preis -> Benachrichtigung
		if lpreis < oldpreis or lshop != oldshop:
			# send email
			if args.email:
				if args.debug:
					print("Sending eMail")
				msg = EmailMessage()
				msg.set_content(mailtxt % (a['name'], oldpreis, lpreis, lurl))
				msg['Subject'] = "Neuer Preis für %s: %.2f" % (a['name'], lpreis)
				msg['From'] = args.mail
				msg['To'] = args.mail
		
				s = SMTP('localhost')
				s.send_message(msg)
				s.quit()
	
			# send to matrix server
			if args.matrix:
				if args.debug:
					print("Sending Matrix message")
				async def send_matrix():
					client = AsyncClient(args.matrix[0], args.matrix[2])
					await client.login(args.matrix[3])
					await client.room_send(
						room_id=args.matrix[1],
						message_type="m.room.message",
						content={"msgtype": "m.text", "body": f"Neuer Preis für {a['name']}: {lpreis}€ (alt: {oldpreis}€)\n{lurl}"}
					)
					await client.close()
				asyncio.run(send_matrix())

			# send telegram message
			if args.telegram:
				if args.debug:
					print("Sending Telegram Message")
					
				params = {"chat_id":args.telegram[1], "text":f"Neuer Preis für {a['name']}: {lpreis}€ (alt: {oldpreis}€)\n{lurl}"}
				message = requests.post(f"https://api.telegram.org/bot{args.telegram[0]}/sendMessage", params=params)

				if args.debug:
					print(message)

			# send signal message
			if args.signal:
				if args.debug:
					print("Sending Signal Message")

				group = args.signal[0]
				sendgroup = []
				for i in b64decode(group.replace("_","/")):
					sendgroup.append(i)

				bus = SystemBus()
				signal = bus.get('org.asamk.Signal')
				account = signal.listAccounts()[0]

				signal2 = bus.get(bus_name='org.asamk.Signal',object_path=account)
				signal2.sendGroupMessage(f"Neuer Preis für {a['name']}: {lpreis}€ (alt: {oldpreis}€)\n{lurl}", [], sendgroup)
		
				if args.debug:
					print(p)

	if args.pause:
		sleep(args.pause[0])

# vim: set ts=4:
