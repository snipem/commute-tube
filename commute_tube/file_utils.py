#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import hashlib

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
    st = os.statvfs(pathToDownloadFolder)
    return st.f_bavail * st.f_frsize / 1024 / 1024 / 1024

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
