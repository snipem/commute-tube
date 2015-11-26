#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from youtube_dl import YoutubeDL
from youtube_dl import version as YoutubeDL_version
import file_utils

import os
import sys
import logging
import json
import shutil
import ntpath
import subprocess


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
        """Load config from config.json"""
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

        if 'delete' in self.config['pen']:
            self.delete = True
            self.deleteStrategy = self.config['pen']['delete']['strategy']
            self.deleteFreeSpace = self.config['pen']['delete']['freeSpace']
            self.deleteExclude = self.config['pen']['delete']['exclude']

        self.pathToDownloadFolder = self.penPath + "/" + self.downloadFolder

    def mount(self):
        """Mounts USB device on given path delivers True if successfull and False
        if not
        """
        if os.path.ismount(self.penPath) == False:
            self.log.info(
                "There is no USB pen mounted under "
                + self.penPath + ". Trying to mount it.")

            if file_utils.mountUSB(self.penPath) == False:
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
        """Unmounts USB device on given path delivers True if successfull and False
        if not
        """
        if file_utils.unmountUSB(self.penPath) == True:
            self.log.info(
                "USB Pen under " + self.penPath + " has been unmounted")
            return True
        else:
            self.log.error(
                "USB Pen under " + self.penPath
                + " has not been successfully unmounted")
            return False

    def processShellscript(self, source):
        """Runs a shellscript and returns it's output line by line as a list"""
        shellscript = source['shellscript']

        self.log.info(
            "Processing shellscript: '" + shellscript + "'")

        out = subprocess.Popen(["bash", "-c", shellscript],
                               stdout=subprocess.PIPE).communicate()[0]
        self.log.debug("Shellscript output: " + out)

        urls = out.split("\n")
        urls = filter(lambda a: a != '', urls)

        return urls

    def processUrl(self, source):
        """Main method for processing urls

        This method basically hands over the configuration to YoutubeDL and repeats
        the step until every source in the configuration was read
        """
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
        prefix = ""

        if 'format' not in ydl.params and 'format_limit' not in ydl.params:
            ydl.params['format'] = "bestvideo+bestaudio/best"
        if 'nooverwrites' not in ydl.params:
            ydl.params['nooverwrites'] = True
        if 'ignoreerrors' not in ydl.params:
            ydl.params['ignoreerrors'] = True
        if 'download_archive' not in ydl.params:
            ydl.params['download_archive'] = "already_downloaded.txt"
        if 'prefix' in ydl.params:
            prefix = ydl.params['prefix']

        ydl.params['restrictfilenames'] = True
        ydl.params['logger'] = self.ydlLog

        outtmpl = self.pathToDownloadFolder + "/" + prefix + \
            u'%(uploader)s-%(title)s-%(id)s.%(ext)s'
        if 'outtmpl' not in ydl.params:
            ydl.params['outtmpl'] = outtmpl

        if self.debug is True:
            self.log.debug(
                "All downloads will be simulated since this is debug mode")
            ydl.params['simulate'] = True

        ydl.download([source['url']])

    def processPath(self, source):
        """Main method for processing paths

        When a path is processed the source file is compared with the possibly
        inplace target file. If different or not existant, the source file is
        copied
        """

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
        elif filesAreDifferent(src, dest):
            shutil.copy2(src, dest)
            self.log.debug(
                "+ File " + filename +
                " did exist but was different, has been overwritten")
            return filename
        else:
            self.log.debug(
                "= File " + filename +
                " has not been copied," +
                " was already in place with same 100 byte digest")



    def run(self):
        """Main method for processing sources

        This method mounts the USB pen, calculates the disk space left before and after,
        runs all sources, one at a time, evaluates a file delta and writes playlists
        for all files and all new files. Finally, the USB pen will be unmounted.
        """
        try:

            if self.mountAndUnmount is True and self.mount() is False:
                sys.exit(1)

            file_utils.createDownloadFolder(self.pathToDownloadFolder)

            if self.delete == True:
                self.log.info("Freeing space")
                if (self.deleteStrategy == "DeleteFolder"):
                    self.log.debug("Using DeleteFolder strategy for deletion")
                    self.freeSpaceByMovingToDeleteFolder(self.pathToDownloadFolder, self.deleteFreeSpace, self.deleteExclude)

            diskSizeBefore = file_utils.getRemainingDiskSizeInGigaByte(self.pathToDownloadFolder)
            filesBefore = os.listdir(self.pathToDownloadFolder)

            self.log.info("Remaining disk size: %.2f GB" % diskSizeBefore)

            downloadedFiles = []

            self.log.debug(
                "Running with YoutubeDL version as of " +
                YoutubeDL_version.__version__)

            for source in self.config['source']:

                try:

                    if "url" in source:
                        filename = self.processUrl(source)
                    elif "path" in source:
                        filename = self.processPath(source)
                    elif "shellscript" in source:
                        urls = self.processShellscript(source)
                        for url in urls:
                            source['url'] = url
                            filename = self.processUrl(source)

                    if (filename is not None):
                        downloadedFiles.append(filename)

                except Exception, e:
                    self.log.error(
                        "Error while processing source. Message: '" +
                        e.message + "'")
                    self.log.exception(e)

            filesAfter = os.listdir(self.pathToDownloadFolder)

            filesDelta = sorted(list(set(filesAfter) - set(filesBefore)))
            for fileDelta in filesDelta:
                downloadedFiles.append(fileDelta)

            downloadedFiles = sorted(downloadedFiles)

            for downloadedFile in downloadedFiles:
                self.log.info("Downloaded: " + downloadedFile)

            diskSizeAfter = file_utils.getRemainingDiskSizeInGigaByte(self.pathToDownloadFolder)
            self.log.info("Remaining disk size: %.2f GB" % diskSizeAfter)

            allFiles = sorted(os.listdir(self.pathToDownloadFolder))

            # TODO Add configuration option here
            if (True):
                self.log.debug("Writing playlist for all files")
                file_utils.writePlaylist(self.pathToDownloadFolder, allFiles, "all")

            # TODO Add configuration option here
            if (True):
                self.log.debug("Writing playlist for new files")
                file_utils.writePlaylist(self.pathToDownloadFolder, downloadedFiles, "new")

            # Copy log file to USB pen
            logFileDestination = self.pathToDownloadFolder + "/" + self.logFile
            shutil.copyfile(self.logFile, logFileDestination)
            self.log.debug("Log file has been copied to " + logFileDestination)

        except Exception, e:
            self.log.exception(e)
            raise e
        finally:
            if self.mountAndUnmount is True:
                self.unmount()

    def checkForPen(self):
        """This method checks if a pen is present or not. Exits with exit code 1
        if not. Else exit code 0."""
        if os.path.ismount(self.penPath) == False:
            self.log.info("USB Pen is not mounted under " + self.penPath)
            if file_utils.mountUSB(self.penPath) == True:
                self.log.info("USB Pen has been successfully mounted")
            else:
                sys.exit(1)

            if file_utils.unmountUSB(self.penPath) == True:
                self.log.info("USB Pen has been successfully unmounted")
            else:
                sys.exit(1)

            self.log.info("USB Pen is present and able to be mounted")
            sys.exit(0)
        else:
            self.log.info("USB Pen is already mounted under " + self.penPath)
            sys.exit(0)


    def freeSpaceByMovingToDeleteFolder(self, pathToDownloadFolder, spaceToFree, exclude):
        self.log.info("Delete 'delete' folder")
        file_utils.deleteFilesInDeleteFolder(pathToDownloadFolder)

        self.log.info("Moving files to 'delete' folder")
        filesToBeMoved = file_utils.getFilenamesForDeletion(pathToDownloadFolder, spaceToFree, exclude)
        file_utils.moveFilesToDeleteFolder(pathToDownloadFolder, filesToBeMoved)

    def main(self):
        self.run()
