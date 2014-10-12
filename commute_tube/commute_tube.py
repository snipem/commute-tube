#!/usr/bin/env python

from youtube_dl import YoutubeDL
import youtube_dl
import os
import sys
import logging
import json
from pprint import pprint
import subprocess

class CommuteTube():

	debug = None
	log = None
	ydlLog = None
	config = []
	penPath = ""
	downloadFolder = ""
	pathToDownloadFolder = ""


	def getConfig(self):
		json_data=open('config.json')
		return json.load(json_data)

	def __init__(self):

		self.debug = False
		self.log = logging.getLogger()
		self.ydlLog = logging.getLogger("youtube_dl")
		self.config = self.getConfig()

		self.penPath = self.config['pen']['penPath']
		self.downloadFolder = self.config['pen']['downloadFolder']
		self.pathToDownloadFolder = self.penPath+"/"+self.downloadFolder

		if self.debug == True:
			self.log.setLevel("DEBUG")

	def mountUSB(self,path):
		subprocess.check_call(["mount", path])
		return True

	def unmountUSB(self,path):
		subprocess.check_call(["umount", path])
		return True

	def run(self):

		if os.path.ismount(self.penPath) == False:
			print ("There is no USB pen mounted under " + self.penPath + ". Trying to mount it.")
			outcomeMount = self.mountUSB(self.penPath)
			
			if outcomeMount == False:
				print ("Could not mount USB pen under " + self.penPath + ". Exiting")
				sys.exit(-1)
			else:
				print ("Successfully mounted USB pen under " + self.penPath)
		else:
			print ("There is a USB pen already mounted under " + self.penPath + ". Processing further.")

		if os.path.exists(self.pathToDownloadFolder) == False:
			print ("Creating folder "+self.pathToDownloadFolder)
			os.mkdir(self.pathToDownloadFolder)

		ydl = YoutubeDL()

		ydl.add_default_info_extractors()

		for source in self.config['source']:
			print source
			
			ydl.params = source
			ydl.params['nooverwrites'] = True
			ydl.params['download_archive'] = "already_downloaded.txt"
			#ydl.params['logger'] = ydlLog
			outtmpl = self.pathToDownloadFolder + u'/%(uploader)s-%(title)s-%(id)s.%(ext)s'
			ydl.params['outtmpl'] = outtmpl

			if self.debug == True:
				self.log.debug("All downloads will be simulated since this is debug mode")
				ydl.params['simulate'] = True

			ydl.download([source['url']])

		if self.unmountUSB(self.penPath) == True:
			print ("USB Pen under "+self.penPath+ " has been unmounted")
			sys.exit(0)
		else:
			print ("USB Pen under "+self.penPath+ " has not been successfully unmounted")
			sys.exit(1)

	def checkForPen(self):
		if os.path.ismount(self.penPath) == False:
			print("USB Pen is not mounted under "+self.penPath)
			if self.mountUSB(self.penPath) == True:
				print("USB Pen has been successfully mounted")
			else:
				sys.exit(1)

			if self.unmountUSB(self.penPath) == True:
				print("USB Pen has been successfully unmounted")
			else:
				sys.exit(1)

			print ("USB Pen is present and able to be mounted")
			sys.exit(0)
		else:
			print("USB Pen is already mounted under "+ self.penPath)
			sys.exit(0)

	def main(self):
		self.run()


