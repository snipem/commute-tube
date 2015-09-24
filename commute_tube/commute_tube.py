#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from youtube_dl import YoutubeDL
from youtube_dl import version as YoutubeDL_version
import os
import sys
import logging
import json
import subprocess
import shutil
import ntpath
import hashlib
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
    downloadedFiles = []
    lastLoggedFracture = 0

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

        #Mute YoutubeDL logger
        consoleHandler = logging.StreamHandler()
        noneLogging = logging.getLogger('testlog')
        noneLogging.addHandler(consoleHandler)
        noneLogging.setLevel(logging.INFO)

        self.log = logging
        self.ydlLog = noneLogging

        self.config = self.getConfig()
        self.penPath = self.config['pen']['penPath']
        self.downloadFolder = self.config['pen']['downloadFolder']

        if self.config['pen']['mountAndUnmount'] == "False":
            self.mountAndUnmount = False
        if self.config['pen']['debug'] == "True":
            self.debug = True

        self.pathToDownloadFolder = self.penPath + "/" + self.downloadFolder

    def _mountUSB(self, path):
        """Mounts device on given path using mount command

        This method will only work on Unix machines
        """
        try:
            subprocess.check_call(["mount", path])
        except Exception, e:
            self.log.error("Could not mount " + path + " Error: " + e.message)
            return False
        return True

    def _unmountUSB(self, path):
        """Unmounts device on given path using umount command

        This method will only work on Unix machines
        """
        try:
            subprocess.check_call(["umount", path])
        except Exception, e:
            self.log.error("Could not unmount " +
                           path + " Error: " + e.message)
            return False
        return True

    def getRemainingDiskSizeInGigaByte(self):
        """Calculates disk size in Gigabytes

        This method is built to work on both OS X and Linux
        """
        st = os.statvfs(self.pathToDownloadFolder)
        return st.f_bavail * st.f_frsize / 1024 / 1024 / 1024

    def mount(self):
        """Mounts USB device on given path delivers True if successfull and False
        if not
        """
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
        """Unmounts USB device on given path delivers True if successfull and False
        if not
        """
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
        """Creates download folder on configured download folder location"""
        if os.path.exists(self.pathToDownloadFolder) == False:
            self.log.info("Creating folder " + self.pathToDownloadFolder)
            os.mkdir(self.pathToDownloadFolder)

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
        ydl.add_progress_hook(self.logHook)

        outtmpl = self.pathToDownloadFolder + "/" + prefix + \
            u'%(uploader)s-%(title)s-%(id)s.%(ext)s'
        if 'outtmpl' not in ydl.params:
            ydl.params['outtmpl'] = outtmpl

        if self.debug is True:
            self.log.debug(
                "All downloads will be simulated since this is debug mode")
            ydl.params['simulate'] = True

        ydl.download([source['url']])

    def logHook(self, d):
        """Hook for intercepting YoutubeDL messages regarding download progress"""
        basename = os.path.basename(d['filename'])

        percentage = float(d['downloaded_bytes']/d['total_bytes']*100)
        fracture = int(percentage/10)

        if d['status'] == 'downloading' and self.lastLoggedFracture != fracture:
            self.log.debug(d['_percent_str'] + " ... " + basename + " downloading at " + d['_speed_str'])
            lastLoggedFracture = fracture

        if d['status'] == 'finished':

            self.log.info("* " + basename + " downloaded with size " + d['_total_bytes_str'])
            self.downloadedFiles.append(basename)
            lastLoggedFracture = 0

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
        elif self.filesAreDifferent(src, dest):
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

    def filesAreDifferent(self, src, dest):
        """Compares the first 100 bytes of two files and returns True if different,
        and False if not

        The comparison of only the first 100 bytes is made for performance reasons.
        Files to be copied are most likely video files and therefore very likely
        different within the first bytes.

        TODO
        This method will be false positive if only the first 100 bytes match. For
        example a not completely copied file will not be different.
        """
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
        """Main method for processing sources

        This method mounts the USB pen, calculates the disk space left before and after,
        runs all sources, one at a time, evaluates a file delta and writes playlists
        for all files and all new files. Finally, the USB pen will be unmounted.
        """
        try:

            if self.mountAndUnmount is True and self.mount() is False:
                sys.exit(1)

            self.createDownloadFolder()

            diskSizeBefore = self.getRemainingDiskSizeInGigaByte()

            self.log.info("Remaining disk size: %.2f GB" % diskSizeBefore)

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
                        self.downloadedFiles.append(filename)

                except Exception, e:
                    print e
                    self.log.error(
                        "Error while processing source. Message: '" +
                        e.message + "'")

            self.downloadedFiles = sorted(self.downloadedFiles)

            for downloadedFile in self.downloadedFiles:
                self.log.info("Downloaded: " + downloadedFile)

            diskSizeAfter = self.getRemainingDiskSizeInGigaByte()
            self.log.info("Remaining disk size: %.2f GB" % diskSizeAfter)

            allFiles = sorted(os.listdir(self.pathToDownloadFolder))

            # TODO Add configuration option here
            if (True):
                self.log.debug("Writing playlist for all files")
                self.writePlaylist(allFiles, "all")

            # TODO Add configuration option here
            if (True):
                self.log.debug("Writing playlist for new files")
                self.writePlaylist(self.downloadedFiles, "new")

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

    def writePlaylist(self, files, name):
        """Writes a playlist consisting of all files given as parameter"""
        f = open(self.pathToDownloadFolder + '/' + name + '.m3u', 'w')
        f.write("\n".join(files).encode('UTF-8'))

    def checkForPen(self):
        """This method checks if a pen is present or not. Exits with exit code 1
        if not. Else exit code 0."""
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
