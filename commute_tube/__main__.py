#!/usr/bin/env python

from youtube_dl import YoutubeDL
import youtube_dl
import os
import sys
import logging
import json
from pprint import pprint

debug = True

log = logging.getLogger()

if debug == True:
	log.setLevel("DEBUG")

def getConfig():

	json_data=open('config.json')

	return json.load(json_data)

linkToPen = "/Volumes/Festplatte/"
downloadFolder = "Download"

pathToDownloadFolder = linkToPen+downloadFolder

if os.path.ismount(linkToPen) == False:
	print ("There is no USB pen mounted under " + linkToPen + ". Exiting.")
	sys.exit(-1)

if os.path.exists(pathToDownloadFolder) == False:
	print ("Creating folder "+pathToDownloadFolder)
	#TODO Create folder

ydl = YoutubeDL()

ydl.add_default_info_extractors()

config = getConfig()

for source in config['source']:
	print source
	ydl.params = source	
	if debug == True:
		log.debug("All downloads will be simulated since this is debug mode")
		ydl.params['simulate'] = True

	ydl.download([source['url']])
