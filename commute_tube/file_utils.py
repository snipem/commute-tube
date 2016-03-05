#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import hashlib
import shutil
import subprocess
import logging
import humanfriendly

logFormatter = logging.Formatter(
    "%(asctime)s [%(levelname)-5.5s] [%(module)-12.12s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler("file_utils.log", mode='w')
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

log = logging

def mountUSB(path):
    """Mounts device on given path using mount command

    This method will only work on Unix machines
    """
    try:
        subprocess.check_call(["mount", path])
    except Exception, e:
        log.exception(e)
        return False
    return True

def unmountUSB(path):
    """Unmounts device on given path using umount command

    This method will only work on Unix machines
    """
    try:
        subprocess.check_call(["umount", path])
    except Exception, e:
        log.exception(e)
        return False
    return True

def createDownloadFolder(pathToDownloadFolder):
    """Creates download folder on configured download folder location"""
    if os.path.exists(pathToDownloadFolder) == False:
        os.mkdir(pathToDownloadFolder)

def getRemainingDiskSizeHumanFriendly(pathToDownloadFolder):
    """Calculates disk size humanfriendly form

    This method is built to work on both OS X and Linux
    """
    return humanfriendly.format_size(getRemainingDiskSizeInByte(pathToDownloadFolder))

def getRemainingDiskSizeInByte(pathToDownloadFolder):
    """Calculates disk size in bytes

    This method is built to work on both OS X and Linux
    """
    st = os.statvfs(pathToDownloadFolder)
    return st.f_bavail * st.f_frsize

def filesAreDifferent(src, dest):
    """Compares the first 100 bytes of two files and returns True if different,
    and False if not

    The comparison of only the first 100 bytes is made for performance reasons.
    Files to be copied are most likely video files and therefore very likely
    different within the first bytes.

    TODO
    This method will be false positive if only the first 100 bytes match. For
    example a not completely copied file will not be different.
    Solution: Compare trailing 100 bytes
    """
    byteSize = 100

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

def writePlaylist(pathToDownloadFolder, files, name):
    """Writes a playlist consisting of all files given as parameter"""
    f = open(pathToDownloadFolder + '/' + name + '.m3u', 'w')
    f.write("\n".join(files).encode('UTF-8'))

def getFilenamesForDeletion(pathToDownloadFolder, spaceToFree, exclude):
    """Frees space in download folder until free space is reached. Files
    can be excluded to be not put into consideration for deletion"""
    filesToBeDeleted = []
    bytesToFree = humanfriendly.parse_size(spaceToFree)

    exclude.append("delete")

    log.debug("Freeing space in " + pathToDownloadFolder + " if " + str(getRemainingDiskSizeInByte(pathToDownloadFolder)) + " < " + str(bytesToFree))
    if (getRemainingDiskSizeInByte(pathToDownloadFolder) < bytesToFree):

        filesInFolder = [os.path.join(pathToDownloadFolder, f) for f in os.listdir(pathToDownloadFolder)]
        files = sorted(filesInFolder, key=os.path.getctime)
        oldFilesInSize = 0

        for file in files:
            head, filename = os.path.split(file)
            size = os.path.getsize(file)

            log.debug("Looking for " +filename + " in ", exclude)

            if (filename not in exclude):
                bytesToBeFreed = oldFilesInSize + size
                filesToBeDeleted.append(file)
                log.debug("Appended " + file)

                if (bytesToBeFreed >= bytesToFree):
                    log.debug(humanfriendly.format_size(bytesToBeFreed) + " where found and are to be moved")
                    break
                else:
                    log.debug(humanfriendly.format_size(bytesToBeFreed) + "/" + humanfriendly.format_size(bytesToFree) + " found for deletion")

    return filesToBeDeleted

def deleteFilesInDeleteFolder(pathToDownloadFolder):
    """Deletes all files in the subfolder 'delete'"""

    if (not os.path.isdir(pathToDownloadFolder+"/delete")):
        os.mkdir(pathToDownloadFolder+"/delete")

    files = sorted(os.listdir(pathToDownloadFolder + "/delete/"))
    for file in files:
        os.remove(pathToDownloadFolder + "/delete/" + file)
        log.debug("Deleted " + file)

def moveFilesToDeleteFolder(pathToDownloadFolder, filesToBeMoved):
    """Moves all files to 'delete' folder"""

    for file in filesToBeMoved:
        head, filename = os.path.split(file)
        shutil.move(file, pathToDownloadFolder + "/delete/" + filename)
        log.debug("Moved " + file + " to delete folder")
