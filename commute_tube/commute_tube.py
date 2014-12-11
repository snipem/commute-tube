#!/usr/bin/env python
from __future__ import division
from youtube_dl import YoutubeDL
import youtube_dl
import os
import sys
import logging
import json
import subprocess
import shutil
import ntpath

class CommuteTube():

	debug = None
	log = None
	ydlLog = None
	config = []
	penPath = ""
	downloadFolder = ""
	pathToDownloadFolder = ""
	logFile = "commute-tube.log"
	mountAndUnmount = True

	def getConfig(self):
		json_data=open('config.json')
		return json.load(json_data)

	def __init__(self):

		logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] [%(module)-12.12s]  %(message)s")
		rootLogger = logging.getLogger()
		rootLogger.setLevel(logging.DEBUG)

		fileHandler = logging.FileHandler(self.logFile, mode='w')
		fileHandler.setFormatter(logFormatter)
		rootLogger.addHandler(fileHandler)

		consoleHandler = logging.StreamHandler()
		consoleHandler.setFormatter(logFormatter)
		rootLogger.addHandler(consoleHandler)


		self.log = logging
		self.ydlLog = logging

		self.config = self.getConfig()
		self.penPath = self.config['pen']['penPath']
		self.downloadFolder = self.config['pen']['downloadFolder']
		
		if self.config['pen']['mountAndUnmount'] == "False" : self.mountAndUnmount = False
		if self.config['pen']['debug'] == "True" : self.debug = True

		self.pathToDownloadFolder = self.penPath+"/"+self.downloadFolder
			

	def _mountUSB(self,path):
		try:
			subprocess.check_call(["mount", path])
		except Exception, e:
			self.log.error("Could not mount "+path)
			return False
		return True

	def _unmountUSB(self,path):
		try:
			subprocess.check_call(["umount", path])
		except Exception, e:
			self.log.error("Could not unmount "+path)
			return False
		return True

	def getRemainingDiskSizeInGigaByte(self):
		st = os.statvfs(self.pathToDownloadFolder)
		return st.f_bavail * st.f_frsize/1024/1024/1024

	def mount(self):
		if os.path.ismount(self.penPath) == False:
			self.log.info ("There is no USB pen mounted under " + self.penPath + ". Trying to mount it.")
						
			if self._mountUSB(self.penPath) == False:
				self.log.info ("Could not mount USB pen under " + self.penPath)
				return False
			else:
				self.log.info ("Successfully mounted USB pen under " + self.penPath)
		else:
			self.log.info ("There is a USB pen already mounted under " + self.penPath + ". Processing further.")

	def unmount(self):
		# Unmount USB pen after all work is done
		if self._unmountUSB(self.penPath) == True:
			self.log.info ("USB Pen under "+self.penPath+ " has been unmounted")
			return True
		else:
			self.log.error ("USB Pen under "+self.penPath+ " has not been successfully unmounted")
			return False

	def createDownloadFolder(self):
		if os.path.exists(self.pathToDownloadFolder) == False:
			self.log.info ("Creating folder "+self.pathToDownloadFolder)
			os.mkdir(self.pathToDownloadFolder)

	def processUrl(self, source):
		
		ydl = YoutubeDL()
		ydl.add_default_info_extractors()

		sourceUrl = source['url'].decode()
		sourceDescription = ""
		
		if 'description' in source: sourceDescription = source['description'].decode()

		self.log.info("Processing source: '" + sourceDescription + "' Url: '" + sourceUrl + "'")

		ydl.params = source
		if 'nooverwrites' not in ydl.params : ydl.params['nooverwrites'] = True
		if 'ignoreerrors' not in ydl.params : ydl.params['ignoreerrors'] = True
		if 'download_archive' not in ydl.params : ydl.params['download_archive'] = "already_downloaded.txt"
		
		ydl.params['logger'] = self.ydlLog
		
		outtmpl = self.pathToDownloadFolder + u'/%(uploader)s-%(title)s-%(id)s.%(ext)s'
		if 'outtmpl' not in ydl.params : ydl.params['outtmpl'] = outtmpl

		if self.debug == True:
			self.log.debug("All downloads will be simulated since this is debug mode")
			ydl.params['simulate'] = True

		ydl.download([source['url']])

	def processPath(self, source):

		sourcePath = source['path'].decode()
		sourceDescription = ""
		if 'description' in source: sourceDescription = source['description'].decode()
		
		self.log.info("Processing path: '" + sourceDescription + "' Path: '" + sourcePath + "'")

		src = sourcePath
		filename = ntpath.basename(sourcePath)
		dest = self.pathToDownloadFolder + "/" + filename

		self.log.debug("Attempt to copy to " + dest)

		if not os.path.isfile(dest):
			shutil.copy2 (src, dest)
			self.log.debug("File "+ filename +" did not exist, has been copied")
		elif os.stat(src).st_mtime - os.stat(dest).st_mtime > 1:
			shutil.copy2 (src, dest)
			self.log.debug("File "+ filename +" did exist but was older, has been overwritten")
		else:
			self.log.debug("File "+ filename +" has not been copied, was already in place with same timestamp")

	def run(self):

		try:

			if self.mountAndUnmount == True and self.mount() == False:
				sys.exit(1)

			self.createDownloadFolder()

			diskSizeBefore = self.getRemainingDiskSizeInGigaByte()
			filesBefore = os.listdir(self.pathToDownloadFolder)

			self.log.info("Remaining disk size: %.2f GB" % diskSizeBefore)


			for source in self.config['source']:
				
				try:
					
					if "url" in source : self.processUrl(source)
					elif "path" in source : self.processPath(source)

				except Exception, e:
					print e
					self.log.error ("Error while processing source. Message: '" + e.message +"'")

			filesAfter = os.listdir(self.pathToDownloadFolder)
		
			filesDelta = list(set(filesAfter) - set(filesBefore))
			for fileDownloaded in filesDelta:
				self.log.info("Downloaded: " + fileDownloaded)

			diskSizeAfter = self.getRemainingDiskSizeInGigaByte()
			self.log.info("Remaining disk size: %.2f GB" % diskSizeAfter)

			# Copy log file to USB pen
			logFileDestination = self.pathToDownloadFolder+ "/" + self.logFile
			shutil.copyfile(self.logFile, logFileDestination)
			self.log.debug("Log file has been copied to " + logFileDestination)

		except Exception, e:
			self.log.error(e)
			raise e
		finally:
			if self.mountAndUnmount == True:
				self.unmount()		

	def checkForPen(self):
		if os.path.ismount(self.penPath) == False:
			self.log.info("USB Pen is not mounted under "+self.penPath)
			if self._mountUSB(self.penPath) == True:
				self.log.info("USB Pen has been successfully mounted")
			else:
				sys.exit(1)

			if self._unmountUSB(self.penPath) == True:
				self.log.info("USB Pen has been successfully unmounted")
			else:
				sys.exit(1)

			self.log.info ("USB Pen is present and able to be mounted")
			sys.exit(0)
		else:
			self.log.info("USB Pen is already mounted under "+ self.penPath)
			sys.exit(0)

	def main(self):
		self.run()


