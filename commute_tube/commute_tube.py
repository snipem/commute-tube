#!/usr/bin/env python
# -*- coding: utf-8 -*-

from youtube_dl import YoutubeDL
from youtube_dl import version as YoutubeDL_version
from youtube_dl.utils import match_filter_func

from . import file_utils
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
    download_archive = None
    logFile = "commute-tube.log"

    def get_config(self):
        """Load config from config path"""
        json_data = open(self.configPath)
        return json.load(json_data)

    def __init__(self, args):
        self.configPath = args.config
        self.source_filter = args.filter
        self.debug = args.debug
        self.download_archive = args.download_archive

        logFormatter = logging.Formatter(
            "%(asctime)s [%(levelname)-5.5s] [%(module)-12.12s] %(message)s")

        rootLogger = logging.getLogger()
        rootLogger.setLevel(logging.DEBUG)

        fileHandler = logging.FileHandler(self.logFile, mode='w')
        fileHandler.setFormatter(logFormatter)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)

        rootLogger.addHandler(fileHandler)
        rootLogger.addHandler(consoleHandler)

        self.log = logging
        self.ydlLog = logging

        self.config = self.get_config()
        self.penPath = args.path if args.path else self.config['pen']['penPath']
        self.downloadFolder = self.config['pen']['downloadFolder']

        if args.format:
            self.config['pen']['common']['format'] = args.format

        self.pathToDownloadFolder = self.penPath + "/" + self.downloadFolder

        file_utils.create_download_folder(self.pathToDownloadFolder)

    def process_shellscript(self, source):
        """Runs a shellscript and returns it's output line by line as a list"""
        shellscript = source['shellscript']

        self.log.info(
            "Processing shellscript: '" + shellscript + "'")

        out = subprocess.Popen(["bash", "-c", shellscript], stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

        # TODO This should be safer
        response = str(out[0].decode("UTF-8"))

        self.log.debug("Shellscript output: '%s'" % response)

        urls = response.split("\n")
        urls = [a for a in urls if a != '']

        return urls

    def process_url(self, source, global_opts):
        """Main method for processing urls

        This method basically hands over the configuration to YoutubeDL and repeats
        the step until every source in the configuration was read
        """

        ydl = YoutubeDL()
        ydl.add_default_info_extractors()

        sourceUrl = source['url']

        sourceDescription = source.get("description", "")

        self._logsource(
            "Processing source: '" + sourceDescription +
            "' Url: '" + sourceUrl + "'", source)

        # Merge local parameters with global ones
        ydl.params = copy.copy(global_opts)
        ydl.params.update(source)

        prefix = ""

        ydl.params['match_filter'] = (
            None if 'match_filter' not in ydl.params or ydl.params['match_filter'] is None
            else match_filter_func(ydl.params['match_filter']))

        # Settings by commute tube over the standard settings, respect if the config sets them differently
        if 'format' not in ydl.params and 'format_limit' not in ydl.params:
            ydl.params['format'] = "bestvideo+bestaudio/best" if 'format' not in self.config else self.config["format"]
        if 'nooverwrites' not in ydl.params:
            ydl.params['nooverwrites'] = True
        if 'ignoreerrors' not in ydl.params:
            ydl.params['ignoreerrors'] = True
        if 'download_archive' not in ydl.params:
            ydl.params['download_archive'] = self.download_archive
        if 'prefix' in ydl.params:
            prefix = ydl.params['prefix']

        ydl.params['restrictfilenames'] = True
        ydl.params['logger'] = self.ydlLog

        outtmpl = self.pathToDownloadFolder + "/" + prefix + \
            '%(uploader)s-%(title)s.%(ext)s'

        if 'outtmpl' not in ydl.params:
            ydl.params['outtmpl'] = outtmpl
        elif not (ydl.params['outtmpl'].startswith(self.pathToDownloadFolder)):
            self._logsource("Prefixing custom set outtmpl with '" + self.pathToDownloadFolder + "/" + prefix + "'", source)
            ydl.params['outtmpl'] = self.pathToDownloadFolder + "/" + prefix + \
                ydl.params['outtmpl']

        if self.debug:
            self._logsource(
                "All downloads will be simulated since this is debug mode", source)
            ydl.params['simulate'] = True

        ydl.download([source['url']])

    def process_path(self, source):
        """Main method for processing paths

        When a path is processed the source file is compared with the possibly
        inplace target file. If different or not existant, the source file is
        copied
        """

        sourcePath = source.get('path')
        sourceDescription = source.get("description", "")

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

        # TODO Use get() instead of direct access of fields
        if "url" in source and not isinstance(source['url'], list):
            filenames.append(self.process_url(source, global_opts))
        elif "url" in source and isinstance(source['url'], list):
            self.log.info("Downloading multiple urls")
            for url in source['url']:
                urls_source = copy.copy(source)
                urls_source['url'] = url
                filenames.append(self.process_url(urls_source, global_opts))
        elif "path" in source:
            filenames.append(self.process_path(source))
        elif "shellscript" in source:
            urls = self.process_shellscript(source)
            for url in urls:
                shellscript_source = copy.copy(source)
                shellscript_source['url'] = url
                filenames.append(self.process_url(shellscript_source, global_opts))

        return filenames

    def run(self):
        """Main method for running commute-tube

        This method calculates the disk space left before and after,
        runs all sources, one at a time, evaluates a file delta and writes playlists
        for all files and all new files.
        """

        file_utils.create_download_folder(self.pathToDownloadFolder)

        diskSizeBefore = file_utils.get_remaining_disk_size_human_friendly(self.pathToDownloadFolder)
        filesBefore = os.listdir(self.pathToDownloadFolder)

        self.log.info("Remaining disk size: " + diskSizeBefore)

        downloadedFiles = []

        self.log.debug(
            "Running with YoutubeDL version as of " +
            YoutubeDL_version.__version__)

        global_opts = self.config.get("pen").get("common", {})

        sources = self.config.get("source")

        if self.source_filter:
            sources = [source for source in sources if source.get("description") == self.source_filter]

        for source in sources:
            try:
                if source.get('deactivated'):
                    self.log.info("Source %s is deactivated", source.get('description'))
                else:
                    filenames = self.process_source(source, global_opts)

                    if (filenames is not None):
                        downloadedFiles + downloadedFiles + filenames

            except Exception as e:
                self.log.error(
                    "Error while processing source. Message: '%s'" % e)
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

    def check_for_pen(self):
        """This method checks if a pen is present or not. Exits with exit code 1
        if not. Else exit code 0."""
        if not os.path.ismount(self.penPath):
            self.log.info("USB Pen is not mounted under " + self.penPath)

            self.log.info("USB Pen is present and able to be mounted")
            sys.exit(0)
        else:
            self.log.info("USB Pen is already mounted under " + self.penPath)
            sys.exit(0)

    def _logsource(self, message, source=None):
        log_description = source.get("description", "")
        self.log.info("[%s] %s" % (log_description, message))

    def main(self):
        self.run()
        sys.exit(0)
