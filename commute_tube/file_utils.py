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

def mount_usb(path):
    """Mounts device on given path using mount command

    This method will only work on Unix machines
    """
    try:
        subprocess.check_call(["mount", path])
    except (Exception) as e:
        log.exception(e)
        return False
    return True

def unmount_usb(path):
    """Unmounts device on given path using umount command

    This method will only work on Unix machines
    """
    try:
        subprocess.check_call(["umount", path])
    except (Exception) as e:
        log.exception(e)
        return False
    return True

def create_download_folder(pathToDownloadFolder):
    """Creates download folder on configured download folder location"""
    if os.path.exists(pathToDownloadFolder) == False:
        os.mkdir(pathToDownloadFolder)

def get_remaining_disk_size_human_friendly(pathToDownloadFolder):
    """Calculates disk size humanfriendly form

    This method is built to work on both OS X and Linux
    """
    return humanfriendly.format_size(get_remaining_disk_size_in_byte(pathToDownloadFolder))

def get_remaining_disk_size_in_byte(pathToDownloadFolder):
    """Calculates disk size in bytes

    This method is built to work on both OS X and Linux
    """
    st = os.statvfs(pathToDownloadFolder)
    return st.f_bavail * st.f_frsize

def files_are_different(src, dest):
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

def write_playlist(pathToDownloadFolder, files, name):
    """Writes a playlist consisting of all files given as parameter"""
    f = open(pathToDownloadFolder + '/' + name + '.m3u', 'w')
    f.write("\n".join(files).encode('UTF-8'))

