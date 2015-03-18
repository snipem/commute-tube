#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from youtube_dl import YoutubeDL
import os
import sys
import logging
import json
import subprocess
import shutil
import ntpath
import hashlib


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
        json_data = open('config.json')
        return json.load(json_data)

    def __init__(self):

        logFormatter = logging.Formatter(
            "%(asctime)s [%(levelname)-5.5s] [%(module)-12.12s]  %(message)s")
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

        if self.config['pen']['mountAndUnmount'] == "False":
            self.mountAndUnmount = False
        if self.config['pen']['debug'] == "True":
            self.debug = True

        self.pathToDownloadFolder = self.penPath + "/" + self.downloadFolder

    def _mountUSB(self, path):
        try:
            subprocess.check_call(["mount", path])
        except Exception, e:
            self.log.error("Could not mount " + path)
            return False
        return True

    def _unmountUSB(self, path):
        try:
            subprocess.check_call(["umount", path])
        except Exception, e:
            self.log.error("Could not unmount " + path)
            return False
        return True

    def getRemainingDiskSizeInGigaByte(self):
        st = os.statvfs(self.pathToDownloadFolder)
        return st.f_bavail * st.f_frsize / 1024 / 1024 / 1024

    def mount(self):
        if os.path.ismount(self.penPath) == False:
            self.log.info(
                "There is no USB pen mounted under "
                + self.penPath + ". Trying to mount it.")

            if self._mountUSB(self.penPath) == False:
                self.log.info("Could not mount USB pen under " + self.penPath)
                return False
            else:
                self.log.info(
                    "Successfully mounted USB pen under " + self.penPath)
        else:
            self.log.info(
                "There is a USB pen already mounted under " + self.penPath
                + ". Processing further.")

    def unmount(self):
        # Unmount USB pen after all work is done
        if self._unmountUSB(self.penPath) == True:
            self.log.info(
                "USB Pen under " + self.penPath + " has been unmounted")
            return True
        else:
            self.log.error(
                "USB Pen under " + self.penPath
                + " has not been successfully unmounted")
            return False

    def createDownloadFolder(self):
        if os.path.exists(self.pathToDownloadFolder) == False:
            self.log.info("Creating folder " + self.pathToDownloadFolder)
            os.mkdir(self.pathToDownloadFolder)

    def processUrl(self, source):

        ydl = YoutubeDL()
        ydl.add_default_info_extractors()

        sourceUrl = source['url'].decode()
        sourceDescription = ""

        if 'description' in source:
            sourceDescription = source['description'].decode()

        self.log.info(
            "Processing source: '" + sourceDescription
            + "' Url: '" + sourceUrl + "'")

        ydl.params = source

        if 'format' not in ydl.params:
            ydl.params['format'] = "bestvideo+bestaudio"
        if 'nooverwrites' not in ydl.params:
            ydl.params['nooverwrites'] = True
        if 'ignoreerrors' not in ydl.params:
            ydl.params['ignoreerrors'] = True
        if 'download_archive' not in ydl.params:
            ydl.params['download_archive'] = "already_downloaded.txt"

        ydl.params['logger'] = self.ydlLog

        outtmpl = self.pathToDownloadFolder + \
            u'/%(uploader)s-%(title)s-%(id)s.%(ext)s'
        if 'outtmpl' not in ydl.params:
            ydl.params['outtmpl'] = outtmpl

        if self.debug is True:
            self.log.debug(
                "All downloads will be simulated since this is debug mode")
            ydl.params['simulate'] = True

        ydl.download([source['url']])

    def processPath(self, source):

        sourcePath = source['path'].decode()
        sourceDescription = ""
        if 'description' in source:
            sourceDescription = source['description'].decode()

        self.log.info(
            "Processing path: '" + sourceDescription +
            "' Path: '" + sourcePath + "'")

        src = sourcePath
        filename = ntpath.basename(sourcePath)
        dest = self.pathToDownloadFolder + "/" + filename

        if not os.path.isfile(dest):
            shutil.copy2(src, dest)
            self.log.debug(
                "+ File " + filename + " did not exist, has been copied")
            return filename
        elif self.filesAreDifferent(src, dest):
            shutil.copy2(src, dest)
            self.log.debug(
                "+ File " + filename + " did exist but was different, has been overwritten")
            return filename
        else:
            self.log.debug(
                "= File " + filename + " has not been copied, was already in place with same 100 byte digest")

    def filesAreDifferent(self, src, dest):
        byteSize = 100

        print src
        print dest
        s = open(src, 'rb')
        srcDigest = hashlib.sha224(s.read(byteSize)).digest()
        d = open(dest, 'rb')
        destDigest = hashlib.sha224(d.read(byteSize)).digest()

        s.close()
        d.close()

        if srcDigest == destDigest:
            return False
        else:
            return True

    def run(self):

        try:

            if self.mountAndUnmount is True and self.mount() is False:
                sys.exit(1)

            self.createDownloadFolder()

            diskSizeBefore = self.getRemainingDiskSizeInGigaByte()
            filesBefore = os.listdir(self.pathToDownloadFolder)

            self.log.info("Remaining disk size: %.2f GB" % diskSizeBefore)

            downloadedFiles = []

            for source in self.config['source']:

                try:

                    if "url" in source:
                        filename = self.processUrl(source)
                    elif "path" in source:
                        filename = self.processPath(source)

                    if (filename is not None):
                        downloadedFiles.append(filename)

                except Exception, e:
                    print e
                    self.log.error(
                        "Error while processing source. Message: '" +
                        e.message + "'")

            filesAfter = os.listdir(self.pathToDownloadFolder)

            filesDelta = list(set(filesAfter) - set(filesBefore))
            for fileDelta in filesDelta:
                downloadedFiles.append(fileDelta)

            for downloadedFile in downloadedFiles:
                self.log.info("Downloaded: " + downloadedFile)

            diskSizeAfter = self.getRemainingDiskSizeInGigaByte()
            self.log.info("Remaining disk size: %.2f GB" % diskSizeAfter)

            # TODO Add configuration option here
            if (True):
                self.log.debug("Writing playlist for new files")
                self.writePlaylist(downloadedFiles)

            # Copy log file to USB pen
            logFileDestination = self.pathToDownloadFolder + "/" + self.logFile
            shutil.copyfile(self.logFile, logFileDestination)
            self.log.debug("Log file has been copied to " + logFileDestination)

        except Exception, e:
            self.log.error(e)
            raise e
        finally:
            if self.mountAndUnmount is True:
                self.unmount()

    def writePlaylist(self, files):
        f = open(self.pathToDownloadFolder + '/' + 'new.m3u', 'w')
        f.write("\n".join(files).encode('UTF-8'))

    def checkForPen(self):
        if os.path.ismount(self.penPath) == False:
            self.log.info("USB Pen is not mounted under " + self.penPath)
            if self._mountUSB(self.penPath) == True:
                self.log.info("USB Pen has been successfully mounted")
            else:
                sys.exit(1)

            if self._unmountUSB(self.penPath) == True:
                self.log.info("USB Pen has been successfully unmounted")
            else:
                sys.exit(1)

            self.log.info("USB Pen is present and able to be mounted")
            sys.exit(0)
        else:
            self.log.info("USB Pen is already mounted under " + self.penPath)
            sys.exit(0)

    def main(self):
        self.run()
