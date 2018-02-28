#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from youtube_dl import YoutubeDL
from youtube_dl import version as YoutubeDL_version
from youtube_dl.utils import match_filter_func

from commute_tube import file_utils
import copy

import os
import sys
import logging
import json
import shutil
import ntpath
import subprocess

class CommuteTube():

    configPath = None
    debug = None
    log = None
    ydlLog = None
    config = []
    penPath = ""
    downloadFolder = ""
    pathToDownloadFolder = ""
    logFile = "commute-tube.log"
    mountAndUnmount = True

    def get_config(self):
        """Load config from config path"""
        json_data = open(self.configPath)
        return json.load(json_data)

    def __init__(self, configPath):
        self.configPath = configPath
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

        self.config = self.get_config()
        self.penPath = self.config['pen']['penPath']
        self.downloadFolder = self.config['pen']['downloadFolder']

        if self.config['pen']['mountAndUnmount'] == "False":
            self.mountAndUnmount = False
        if self.config['pen']['debug'] == "True":
            self.debug = True

        self.pathToDownloadFolder = self.penPath + "/" + self.downloadFolder

    def mount(self):
        """Mounts USB device on given path delivers True if successfull and False
        if not
        """
        if os.path.ismount(self.penPath) == False:
            self.log.info(
                "There is no USB pen mounted under "
                + self.penPath + ". Trying to mount it.")

            if file_utils.mount_usb(self.penPath) == False:
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
        if file_utils.unmount_usb(self.penPath) == True:
            self.log.info(
                "USB Pen under " + self.penPath + " has been unmounted")
            return True
        else:
            self.log.error(
                "USB Pen under " + self.penPath
                + " has not been successfully unmounted")
            return False

    def process_shellscript(self, source):
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

    def process_url(self, source, global_opts):
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

        # Merge local parameters with global ones
        ydl.params = copy.copy(global_opts)
        ydl.params.update(source)

        prefix = ""

        ydl.params['match_filter'] = (
            None if 'match_filter' not in ydl.params or ydl.params['match_filter'] is None
            else match_filter_func(ydl.params['match_filter']))

        if 'format' not in ydl.params and 'format_limit' not in ydl.params:
            ydl.params['format'] = "bestvideo+bestaudio/best" if 'format' not in self.config else self.config["format"]
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
            u'%(uploader)s-%(title)s.%(ext)s'

        if 'outtmpl' not in ydl.params:
            ydl.params['outtmpl'] = outtmpl
        elif not (ydl.params['outtmpl'].startswith(self.pathToDownloadFolder)):
            self.log.info("Prefixing custom set outtmpl with '" + self.pathToDownloadFolder + "/" + prefix + "'")
            ydl.params['outtmpl'] = self.pathToDownloadFolder + "/" + prefix + \
            ydl.params['outtmpl']

        if self.debug is True:
            self.log.debug(
                "All downloads will be simulated since this is debug mode")
            ydl.params['simulate'] = True

        ydl.download([source['url']])

    def process_path(self, source):
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
        elif file_utils.files_are_different(src, dest):
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


    def process_source(self, source, global_opts):
        """Main method for processing sources

        This method determines the nature of the source and invokes
        source specific behaviour.
        """

        filenames = []

        #TODO Use get() instead of direct access of fields
        if "url" in source and not isinstance(source['url'], list):
            filenames.append(self.process_url(source,global_opts))
        elif "url" in source and isinstance(source['url'], list):
            self.log.info("Downloading multiple urls")
            for url in source['url']:
                urls_source = copy.copy(source)
                urls_source['url'] = url
                filenames.append(self.process_url(urls_source,global_opts))
        elif "path" in source:
            filenames.append(self.process_path(source))
        elif "shellscript" in source:
            urls = self.process_shellscript(source)
            for url in urls:
                shellscript_source = copy.copy(source)
                shellscript_source['url'] = url
                filenames.append(self.process_url(shellscript_source,global_opts))

        return filenames

    def run(self):
        """Main method for running commute-tube

        This method mounts the USB pen, calculates the disk space left before and after,
        runs all sources, one at a time, evaluates a file delta and writes playlists
        for all files and all new files. Finally, the USB pen will be unmounted.
        """
        try:

            if self.mountAndUnmount is True and self.mount() is False:
                sys.exit(1)

            file_utils.create_download_folder(self.pathToDownloadFolder)

            diskSizeBefore = file_utils.get_remaining_disk_size_human_friendly(self.pathToDownloadFolder)
            filesBefore = os.listdir(self.pathToDownloadFolder)

            self.log.info("Remaining disk size: " + diskSizeBefore)

            downloadedFiles = []
            from pprint import pprint

            self.log.debug(
                "Running with YoutubeDL version as of " +
                YoutubeDL_version.__version__)

            if "common" in self.config["pen"]:
                global_opts = self.config["pen"]["common"]
            else:
                global_opts = {}

            for source in self.config['source']:
                try:
                    if source.get('deactivated'):
                        self.log.info("Source %s is deactivated", source.get('description'))
                    else:
                        filenames = self.process_source(source,global_opts)

                        if (filenames is not None):
                            downloadedFiles + downloadedFiles + filenames

                except (Exception) as e:
                    self.log.error(
                        "Error while processing source. Message: '" +
                        e.message + "'")
                    self.log.exception(e)

            filesAfter = os.listdir(self.pathToDownloadFolder)

            filesDelta = sorted(list(set(filesAfter) - set(filesBefore)))
            downloadedFiles = downloadedFiles + filesDelta

            downloadedFiles = sorted(downloadedFiles)

            for downloadedFile in downloadedFiles:
                self.log.info("Downloaded: " + downloadedFile)

            diskSizeAfter = file_utils.get_remaining_disk_size_human_friendly(self.pathToDownloadFolder)
            self.log.info("Remaining disk size: " + diskSizeAfter)

            allFiles = sorted(os.listdir(self.pathToDownloadFolder))

            # TODO Add configuration option here
            if (True):
                self.log.debug("Writing playlist for all files")
                file_utils.write_playlist(self.pathToDownloadFolder, allFiles, "all")

            # TODO Add configuration option here
            if (True):
                self.log.debug("Writing playlist for new files")
                file_utils.write_playlist(self.pathToDownloadFolder, downloadedFiles, "new")

            # Copy log file to USB pen
            logFileDestination = self.pathToDownloadFolder + "/" + self.logFile
            shutil.copyfile(self.logFile, logFileDestination)
            self.log.debug("Log file has been copied to " + logFileDestination)

        except (Exception) as e:
            self.log.exception(e)
            raise e
        finally:
            if self.mountAndUnmount is True:
                self.unmount()

    def check_for_pen(self):
        """This method checks if a pen is present or not. Exits with exit code 1
        if not. Else exit code 0."""
        if os.path.ismount(self.penPath) == False:
            self.log.info("USB Pen is not mounted under " + self.penPath)
            if file_utils.mount_usb(self.penPath) == True:
                self.log.info("USB Pen has been successfully mounted")
            else:
                sys.exit(1)

            if file_utils.unmount_usb(self.penPath) == True:
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

