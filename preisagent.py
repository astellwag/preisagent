#!/usr/bin/python3

import sys
import argparse
from urllib.request import urlopen
from re import findall
from smtplib import SMTP
from email.message import EmailMessage
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action="store_true", help="enable debug output")
parser.add_argument("-m", "--mail", help="send email to address")
args = parser.parse_args()

mailtxt="""\
Hi,

der Preis für %s ist gefallen.

Alter Preis: %d
Neuer Preis: %d

Link zum Artikel: https://www.thomann.de/de/%s

Cheers,
Dein Thomann-Preisagent
"""

home = str(Path.home())
confdir = home + "/.preisagent/"
listfile = confdir + "artikel.txt"

# read list of articles to watch for
artikel=[]

try:
	with open(listfile) as a:
		lines = a.readlines()
except IOError:
		sys.exit("Keine Artikelliste in %s gefunden" % listfile)

for line in lines:
	artikel.append(line.split(","))

# check every article
for art in artikel:
	if args.debug:
		print("Checking " + art[0].strip())
	filename = confdir + art[1].strip()
	url = "https://www.thomann.de/de/" + art[1].strip() + ".htm"

	try:
		with open(filename) as f:
			oldprice=(float(f.readlines()[0]))
	except IOError:
			oldprice=99999999999.9


	html = urlopen(url).read().decode("UTF-8")
	r1 = findall(r"<meta itemprop=\"price\" content=\"\d+\.\d+\">", html)[0]
	price = float(findall(r"\d+\.\d+", r1)[0])
	if args.debug:
		print("Alter Preis: %.2f\nNeuer Preis: %.2f" % (oldprice, price))
	if(price < oldprice):
		if args.debug:
			print("Storing new price")
		with open(filename,"w") as f:
			f.write(str(price) + "\n")
	
		if args.mail:
			if args.debug:
				print("Sending eMail")
			msg = EmailMessage()
			msg.set_content(mailtxt % (art[0].strip(), oldprice, price, art[1]))
			msg['Subject'] = "Neuer Preis für %s" % art[0]
			msg['From'] = args.mail
			msg['To'] = args.mail
	
			s = SMTP('localhost')
			s.send_message(msg)
			s.quit()




# vim: set ts=4:
