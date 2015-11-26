#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import hashlib
import shutil

def mountUSB(path):
    """Mounts device on given path using mount command

    This method will only work on Unix machines
    """
    try:
        subprocess.check_call(["mount", path])
    except Exception, e:
        return False
    return True

def unmountUSB(path):
    """Unmounts device on given path using umount command

    This method will only work on Unix machines
    """
    try:
        subprocess.check_call(["umount", path])
    except Exception, e:
        return False
    return True

def createDownloadFolder(pathToDownloadFolder):
    """Creates download folder on configured download folder location"""
    if os.path.exists(pathToDownloadFolder) == False:
        os.mkdir(pathToDownloadFolder)

def getRemainingDiskSizeInGigaByte(pathToDownloadFolder):
    """Calculates disk size in Gigabytes

    This method is built to work on both OS X and Linux
    """
    return getRemainingDiskSizeInByte(pathToDownloadFolder) / 1024 / 1024 / 1024

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
    import humanfriendly
    print pathToDownloadFolder
    filesToBeDeleted = []
    bytesToFree = humanfriendly.parse_size(spaceToFree)

    exclude.append("delete")

    if (getRemainingDiskSizeInByte(pathToDownloadFolder) < bytesToFree):

        filesInFolder = [os.path.join(pathToDownloadFolder, f) for f in os.listdir(pathToDownloadFolder)]
        #filesInFolder = os.listdir(pathToDownloadFolder)
        print filesInFolder
        files = sorted(filesInFolder, key=os.path.getctime)
        oldFilesInSize = 0

        for file in files:
            head, filename = os.path.split(file)
            size = os.path.getsize(file)

            if (filename not in exclude):
                bytesToBeFreed = oldFilesInSize + size
                filesToBeDeleted.append(file)

                if (bytesToBeFreed >= bytesToFree):
                    break

    return filesToBeDeleted

def deleteFilesInDeleteFolder(pathToDownloadFolder):
    """Deletes all files in the subfolder 'delete'"""

    if (not os.path.isdir(pathToDownloadFolder+"/delete")):
        os.mkdir(pathToDownloadFolder+"/delete")

    files = sorted(os.listdir(pathToDownloadFolder + "/delete/"))
    for file in files:
        os.remove(pathToDownloadFolder + "/delete/" + file)

def moveFilesToDeleteFolder(pathToDownloadFolder, filesToBeMoved):
    """Moves all files to 'delete' folder"""

    for file in filesToBeMoved:
        head, filename = os.path.split(file)
        shutil.move(file, pathToDownloadFolder + "/delete/" + filename)
