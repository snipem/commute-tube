#!/usr/bin/env python

from youtube_dl import YoutubeDL
import youtube_dl
import os
import sys
import logging
import json
from pprint import pprint
import subprocess


debug = False

log = logging.getLogger()
ydlLog = logging.getLogger("youtube_dl")

if debug == True:
	log.setLevel("DEBUG")

def mountUSB(path):
	subprocess.check_call(["mount", path])
	return True

def unmountUSB(path):
	subprocess.check_call(["umount", path])
	return True

def getConfig():
	json_data=open('config.json')
	return json.load(json_data)

config = getConfig()

penPath = config['pen']['penPath']
downloadFolder = config['pen']['downloadFolder']
pathToDownloadFolder = penPath+"/"+downloadFolder

if os.path.ismount(penPath) == False:
	print ("There is no USB pen mounted under " + penPath + ". Trying to mount it.")
	outcomeMount = mountUSB(penPath)
	
	if outcomeMount == False:
		print ("Could not mount USB pen under " + penPath + ". Exiting")
		sys.exit(-1)
	else:
		print ("Successfully mounted USB pen under " + penPath)
else:
	print ("There is a USB pen already mounted under " + penPath + ". Processing further.")

if os.path.exists(pathToDownloadFolder) == False:
	print ("Creating folder "+pathToDownloadFolder)
	os.mkdir(pathToDownloadFolder)

ydl = YoutubeDL()

ydl.add_default_info_extractors()

for source in config['source']:
	print source
	
	ydl.params = source
	ydl.params['nooverwrites'] = True
	ydl.params['download_archive'] = "already_downloaded.txt"
	#ydl.params['logger'] = ydlLog
	outtmpl = pathToDownloadFolder + u'/%(title)s-%(id)s.%(ext)s'
	ydl.params['outtmpl'] = outtmpl

	if debug == True:
		log.debug("All downloads will be simulated since this is debug mode")
		ydl.params['simulate'] = True

	ydl.download([source['url']])

if unmountUSB(penPath) == True:
	print ("USB Pen under "+penPath+ " has been unmounted")
	sys.exit(0)
else:
	print ("USB Pen under "+penPath+ " has not been Successfully unmounted")
	sys.exit(1)

