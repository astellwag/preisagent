#!/usr/bin/python3

import re
from urllib.request import urlopen

configfile = "/home/alex/src/preisagent/preisagent.ini"
mode = "none"
shops = {}
articles = {}

# read configfile
with open(configfile) as c:
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
#	print(a['name'])
#	print("=======================================")
	for sho in a['shops']:
		s = shops[sho]
		url = s['baseurl'] + a['shops'][sho] + s['append']
#		print(url)
#		print(s['matchre'])
		html = urlopen(url).read().decode("UTF-8")
		if re.search(s['matchre'], html):
#			print("match")
#			print(re.search(s['matchre'], html).group(1))
			p = re.search(s['matchre'], html).group(1)
			if p.find(","):
				preis = float(p.replace(",","."))
			else:
				preis = float(p)

			print( a['name'] + " kostet bei " + s['name'] + " " + str(preis) + "€")
#	print()


# vim: set ts=4:
