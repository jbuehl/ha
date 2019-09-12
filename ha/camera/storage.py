# camera storage management
storageDevice = "/mnt/disk1"
storageUpdateInterval = 60
purgeStorageInterval = 60*60*24 # daily
videoRetention = 10

import os
import time
import datetime
import subprocess
import json
from ha import *
from ha.camera.classes import *

# get the number of events and storage used
def getStorageStats(cameraBase, cameras, repeat):
    debug('debugEnable', "starting storage stats thread")
    repeating = True
    while repeating:
        todaysDatetime = datetime.datetime(*time.localtime()[0:6])
        startTimeDatetime = todaysDatetime - datetime.timedelta(days=videoRetention)
        eventStorage = {}
        for camera in sorted(cameras.keys()):
            debug('debugStorage', "getting eventStorage for camera", camera)
            dayDatetime = startTimeDatetime
            for day in range(videoRetention):
                updateStorageStats(camera, time.strftime("%Y%m%d", dayDatetime.timetuple()), cameraBase, eventStorage)
                dayDatetime += datetime.timedelta(days=1)
        debug('debugStorage', "eventStorage", eventStorage)
        json.dump(eventStorage, open(cameraBase+"storage.json", "w"))
        debug('debugEnable', "saved storage stats")
        repeating = repeat
        time.sleep(storageUpdateInterval)

# return the number of events and video storage for the specified camera and day
def updateStorageStats(camera, day, cameraBase, eventStorage):
    videoBase = cameraBase+camera+"/videos/"
    imageBase = cameraBase+camera+"/images/"
    dayDir = day[0:4]+"/"+day[4:6]+"/"+day[6:8]
    nEvents = getEvents(imageBase+dayDir+"/")
    size = getSize(videoBase+dayDir+"/")
    eventStorage[camera+"/"+dayDir] = [nEvents, size]

# get number of events in the specified directory
def getEvents(path):
    try:
        eventFiles = os.listdir(path)
        return str(len(eventFiles))
    except OSError:
        return "0"

# get the sizes of the files in the specified directory
def getSize(path):
    try:
        fileSize = subprocess.check_output("du -h "+path, shell=True)
        return fileSize.split("\t")[0]
    except subprocess.CalledProcessError:
        return "0"

# get the capacity, used, and free space on the specified device
def getStorage(device):
    storage = subprocess.check_output("df -h "+device, shell=True).split("\n")[1].split()
    return storage[1:5]

# delete video older than the specified number of days
def purgeStorage(camera, repeat):
    repeating = True
    while repeating:
        debug('debugEnable', "deleting video older than", videoRetention, "days for camera", camera)
        if videoRetention > 0:
            os.popen("/usr/bin/find "+cameraBase+camera+"/videos"+" -mtime +"+str(videoRetention)+" -type f -delete")
        repeating = repeat
        time.sleep(purgeStorageInterval)
